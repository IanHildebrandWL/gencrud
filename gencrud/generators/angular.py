#
#   Python backend and Angular frontend code generation by gencrud
#   Copyright (C) 2018-2019 Marc Bertens-Nguyen m.bertens@pe2mbs.nl
#
#   This library is free software; you can redistribute it and/or modify
#   it under the terms of the GNU Library General Public License GPL-2.0-only
#   as published by the Free Software Foundation; either version 2 of the
#   License, or (at your option) any later version.
#
#   This library is distributed in the hope that it will be useful, but
#   WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
#   Library General Public License for more details.
#
#   You should have received a copy of the GNU Library General Public
#   License GPL-2.0-only along with this library; if not, write to the
#   Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
#   Boston, MA 02110-1301 USA
#
import copy
import json
import os
import posixpath
import shutil
import sys
import logging
from mako.template import Template
from mako import exceptions
import gencrud.util.utils
import gencrud.util.exceptions
from gencrud.generators.typescript_obj import TypeScript
from gencrud.util.positon import PositionInterface
from gencrud.util.sha import sha256sum

logger = logging.getLogger()

LABEL_APP_ROUTES    = 'const appRoutes: Routes ='
LABEL_NG_MODULE     = '@NgModule('
APP_MODULE          = 'app.module.ts'
APP_ROUTING_MODULE  = 'app.routingmodule.ts'
NG_ENTRY_COMPONENTS = 'entryComponents'
NG_IMPORTS          = 'imports'
NG_PROVIDERS        = 'providers'
NG_DECLARATIONS     = 'declarations'


def makeAngularModule( root_path, *args ):
    if len( args ) > 0:
        modulePath = os.path.join( root_path, args[ 0 ] )
        if not os.path.isdir( modulePath ):
            os.mkdir( modulePath )

        makeAngularModule( modulePath, *args[ 1: ] )

    return


def updateImportSection( lines, files ):
    rangePos = PositionInterface()
    stage = 0
    for lineNo, lineText in enumerate( lines ):
        lineText = lineText.strip( ' \n' )
        if stage == 0 and lineText.startswith( 'import' ):
            if lineText.endswith( ';' ):
                rangePos.end = lineNo

            else:
                stage = 1

        elif stage == 1:
            if lineText.endswith( ';' ):
                stage = 0
                rangePos.end = lineNo

    rangePos.end += 1
    for imp in files:
        foundLine = False
        for lineNo in rangePos.range():
            if imp in lines[ lineNo ]:
                foundLine = True
                break

        if not foundLine:
            lines.insert( rangePos.end, imp + '\n' )
            rangePos.end += 1


def updateAngularAppModuleTs( config, app_module, exportsModules ):
    logger.debug( config.angular.sourceFolder )

    # File to edit 'app.module.ts'
    # inject the following;
    #   inport
    #   declarations:       search for 'declarations: ['
    #   imports:            search for 'imports: ['
    #   providers:          search for 'providers: ['
    #   entryComponents:    search for 'entryComponents: ['
    with open( os.path.join( config.angular.sourceFolder, APP_MODULE ), 'r' ) as stream:
        lines = stream.readlines()

    gencrud.util.utils.backupFile( os.path.join( config.angular.sourceFolder, APP_MODULE ) )
    rangePos        = PositionInterface()
    sectionLines    = gencrud.util.utils.searchSection( lines,
                                                        rangePos,
                                                        LABEL_NG_MODULE + '{',
                                                      '})' )
    pos = sectionLines[0].find( '{' )
    sectionLines[ 0 ] = sectionLines[ 0 ][ pos: ]
    pos = sectionLines[ -1 ].find( '}' )
    sectionLines[ -1 ] = sectionLines[ -1 ][ : pos + 1 ]

    ts = TypeScript()
    NgModule = ts.parse( ''.join( sectionLines ) )

    def updateNgModule( section ):
        for decl in app_module[ section ]:
            if decl != '' and decl not in NgModule[ section ]:
                NgModule[ section ].append( decl )

    updateNgModule( NG_DECLARATIONS )
    updateNgModule( NG_PROVIDERS )
    updateNgModule( NG_IMPORTS )
    updateNgModule( NG_ENTRY_COMPONENTS )

    buffer = LABEL_NG_MODULE + ts.build( NgModule, 2 ) + ')'
    bufferLines = [ '{}\n'.format ( x ) for x in buffer.split( '\n' ) ]
    gencrud.util.utils.replaceInList( lines, rangePos, bufferLines )

    updateImportSection( lines, app_module[ 'files' ] )
    with open( os.path.join( config.angular.sourceFolder, APP_MODULE ), 'w' ) as stream:
        for line in lines:
            stream.write( line )
            logger.debug( line.replace( '\n', '' ) )

    return


def updateAngularAppRoutingModuleTs( config, app_module ):
    if not os.path.isfile( os.path.join( config.angular.sourceFolder, APP_ROUTING_MODULE ) ):
        return []

    with open( os.path.join( config.angular.sourceFolder, APP_ROUTING_MODULE ), 'r' ) as stream:
        lines = stream.readlines()

    gencrud.util.utils.backupFile( os.path.join( config.angular.sourceFolder, APP_ROUTING_MODULE ) )
    imports = []
    entries = []
    for cfg in config:
        if cfg.menu is not None and cfg.menu.menu is not None:
            # Do we have child pages for new and edit?
            children = []
            for action in cfg.actions:
                logger.info( "Action: {} {} {}".format( config.application, cfg.name, action ) )
                if action.type == 'screen' and action.isAngularRoute():
                    logger.info( "Screen {} {} {}".format( config.application, cfg.name, action ) )
                    children.append( {  'path': "'{}'".format( action.route.name ),
                                        'component': "{}".format( action.route.cls ),
                                        'data': {
                                            'title': "'{cls} {label}'".format( cls = cfg.cls,
                                                                               label = action.route.label ),
                                            'breadcrum': "'{}'".format( action.route.label )
                                        }
                                      } )
                    filename = 'table.component' if action.route.cls.endswith( 'TableComponent' ) else 'screen.component'
                    clsmod = cfg.name if action.route.module is None else action.route.module
                    component = "import {{ {cls} }} from './{app}/{module}/{filename}';".format( cls = action.route.cls,
                                                                                                 app = config.application,
                                                                                                 module = clsmod,
                                                                                                 filename = filename )
                    if component not in imports:
                        imports.append( component )

            logger.info( "Action children: {} path {}".format( json.dumps( children, indent = 4 ), cfg.menu.menu.route[ 1: ] ) )
            if len( children ) > 0:
                children.insert( 0, {
                    'path':      "''",
                    'component': '{cls}TableComponent'.format( cls = cfg.cls ),
                    'data':      { 'title':     "'{cls} table'".format( cls = cfg.cls ),
                                   'breadcrum': "'{}'".format( cfg.cls ) }
                } )
                routeItem = { 'path': "'{}'".format( cfg.menu.menu.route[ 1: ] ), 'children': children }

            else:
                routeItem = {
                    'path':      "'{}'".format( cfg.menu.menu.route[ 1: ] ),
                    'component': '{cls}TableComponent'.format( cls = cfg.cls ),
                    'data':      { 'title':     "'{cls} table'".format( cls = cfg.cls ),
                                   'breadcrum': "'{}'".format( cfg.cls ) }
                }

            entries.append( routeItem )

        logger.info( "Inports: {} {} {}".format( config.application, cfg.name, cfg.cls ) )
        component = "import {{ {cls}TableComponent }} from './{app}/{mod}/table.component';".format( cls = cfg.cls ,
                                                                                                     app = config.application,
                                                                                                     mod = cfg.name )
        if component not in imports:
            imports.append( component )

    rangePos = PositionInterface()
    sectionLines = gencrud.util.utils.searchSection( lines,
                                                     rangePos,
                                                     LABEL_APP_ROUTES,
                                                   ']' )
    pos = sectionLines[ 0 ].find( '[' )
    sectionLines[ 0 ] = sectionLines[ 0 ][ pos: ]
    pos = sectionLines[ -1 ].find( ']' )
    sectionLines[ -1 ] = sectionLines[ -1 ][ : pos + 1 ]

    ts = TypeScript()
    appRoutes = ts.parse( ''.join( sectionLines ) )
    for entry in entries:
        logger.debug( "Route: {}".format( json.dumps( entry ) ) )

        routeIdx = -1
        for idx, route in enumerate( appRoutes ):
            if route[ 'path' ] == entry[ 'path' ]:
                logger.info( "Found route: {}".format( route[ 'path' ] ) )
                logger.info( json.dumps( route ) )
                routeIdx = idx
                break

        if routeIdx == -1:
            appRoutes.insert( -1, entry )

        else:
            appRoutes[ routeIdx ] = entry

    buffer = LABEL_APP_ROUTES + ' ' + ts.build( appRoutes, 2 ) + ';'
    bufferLines = [ '{}\n'.format( x ) for x in buffer.split( '\n' ) ]
    gencrud.util.utils.replaceInList( lines, rangePos, bufferLines )

    updateImportSection( lines, imports )
    with open( os.path.join( config.angular.sourceFolder, APP_ROUTING_MODULE ), 'w' ) as stream:
        for line in lines:
            stream.write( line )
            logger.debug( line.replace( '\n', '' ) )

    return imports


def exportAndType( line ):
    return line.split( ' ' )[ 1 : 3 ]


def generateAngular( templates, config ):
    modules = []
    if not os.path.isdir( config.angular.sourceFolder ):
        os.makedirs( config.angular.sourceFolder )

    for cfg in config:
        modulePath = os.path.join( config.angular.sourceFolder,
                                   config.application,
                                   cfg.name )
        if os.path.isdir( modulePath ) and not gencrud.util.utils.overWriteFiles:
            raise gencrud.util.exceptions.ModuleExistsAlready( cfg, modulePath )

        makeAngularModule( config.angular.sourceFolder,
                           config.application,
                           cfg.name )
        for templ in templates:
            templateFilename = os.path.join( config.angular.sourceFolder,
                                             config.application,
                                             cfg.name,
                                             gencrud.util.utils.sourceName( templ ) )
            if templ.endswith( 'module.ts.template' ):
                # This handled by createAngularComponentModule()
                continue

            if os.path.isfile( templateFilename ):
                # First remove the old file
                os.remove( templateFilename )

            logger.info( 'template    : {0}'.format( templ ) )
            if 'screen' in templ:
                logger.info( 'Action new  : {0}'.format( cfg.actions.get( 'new' ).type ) )
                logger.info( 'Action edit : {0}'.format( cfg.actions.get( 'edit' ).type ) )
                if 'screen' in templ and 'screen' in (cfg.actions.get( 'new' ).type,cfg.actions.get( 'edit' ).type):
                    logger.info( "Adding screen for {}".format( templ ) )

                else:
                    logger.info( "Not adding {}".format( templ ) )
                    continue

            elif 'dialog' in templ:
                logger.info( 'Action new  : {0}'.format( cfg.actions.get( 'new' ).type ) )
                logger.info( 'Action edit : {0}'.format( cfg.actions.get( 'edit' ).type ) )
                if 'component' in templ and 'dialog' in ( cfg.actions.get( 'new' ).type, cfg.actions.get( 'edit' ).type ):
                    logger.info( "Adding dialog for {}".format( templ ) )

                elif 'delete' in templ and cfg.actions.get( 'delete' ).type == 'dialog':
                    logger.info( "Adding dialog for {}".format( templ ) )

                else:
                    logger.info( "Not adding {}".format( templ ) )
                    continue

            else:
                pass

            logger.info( 'template    : {0}'.format( templ ) )
            logger.info( 'application : {0}'.format( config.application ) )
            logger.info( 'name        : {0}'.format( cfg.name ) )
            logger.info( 'class       : {0}'.format( cfg.cls ) )
            logger.info( 'table       : {0}'.format( cfg.table.name ) )
            for col in cfg.table.columns:
                logger.info( '- {0:<20}  {1}'.format( col.name, col.sqlAlchemyDef() ) )

            for imp in cfg.table.tsInports:
                logger.info( '  {0}  {1}'.format( imp.module, imp.name ) )

            for imp in cfg.table.pyInports:
                logger.info( '  {0}  {1}'.format( imp.module, imp.name ) )

            logger.info( 'primary key : {0}'.format( cfg.table.primaryKey ) )
            logger.info( 'uri         : {0}'.format( cfg.uri ) )
            with open( templateFilename,
                       gencrud.util.utils.C_FILEMODE_WRITE ) as stream:
                def errorHandler( context, error, *args, **kwargs ):
                    print( context )
                    print( error )
                    print( args )
                    print( kwargs )
                    return

                try:
                    for line in Template( filename = os.path.abspath( templ ) ).render( obj = cfg ).split( '\n' ):
                        if line.startswith( 'export ' ):
                            modules.append( (config.application,
                                             cfg.name,
                                             gencrud.util.utils.sourceName( templ ),
                                             exportAndType( line ) ) )

                        stream.write( line )
                        if sys.platform.startswith( 'linux' ):
                            stream.write( '\n' )

                except Exception as exc:
                    print( "Mako exception:" )
                    for line in exceptions.text_error_template().render_unicode().encode('ascii').split(b'\n'):
                        print( line )

                    print( "Mako done" )
                    raise

    appModule = None
    exportsModules = []
    for app, mod, source, export in modules:
        # Update 'app.module.json'
        app_module_json_file = os.path.join( config.angular.sourceFolder,
                                             app,
                                             mod,
                                             'app.module.json' )
        if os.path.isfile( app_module_json_file ):
            with open( app_module_json_file, 'r' ) as stream:
                try:
                    data = json.load( stream )

                except:
                    logger.error( "Error in file: {0}".format( app_module_json_file ) )
                    raise

                if appModule is None:
                    appModule = data

                else:
                    appModule = gencrud.util.utils.joinJson( appModule, data )

            os.remove( app_module_json_file )

        exportsModules.append( { 'application':   app,
                                 'modules':       mod,
                                 'source':        source,
                                 'export':        export } )

    # Write update 'app.module.json'
    with open( os.path.join( config.angular.sourceFolder, 'app.module.json' ), 'w' ) as stream:
        json.dump( appModule, stream, indent = 4 )

    logger.info( 'exportsModules' )

    for mod in exportsModules:
        logger.info( mod )


    logger.info( 'appModule' )
    for mod in appModule:
        logger.info( mod.strip( '\n' ) )

    imports = updateAngularAppRoutingModuleTs( config,appModule )
    for imp in imports:
        if imp not in appModule[ 'files' ]:
            appModule[ 'files' ].append( imp )


    appModule = createAngularComponentModuleTs( config, appModule )

    logger.info( "appModule: {}".format( json.dumps( appModule, indent = 4 ) ) )
    updateAngularAppModuleTs( config, appModule, exportsModules )

    os.remove( os.path.join( config.angular.sourceFolder, 'app.module.json' ) )
    copyAngularCommon( os.path.abspath( os.path.join( os.path.dirname( __file__ ),
                                                      '..',
                                                      'common-ts' ) ),
                       os.path.join( config.angular.sourceFolder, 'common' ) )
    return


def createAngularComponentModuleTs( config, appModule ):
    if not gencrud.util.utils.useModule:
        return appModule

    templ = os.path.abspath( os.path.join( config.angular.templateFolder, 'module.ts.templ' ) )
    imports = []
    for cfg in config:
        filename = os.path.join( config.application, '{}.module.ts.templ'.format( cfg.name ) )
        # Create the '<name>-module.ts'
        with open( filename, 'w' ) as stream:
            for line in Template( filename = templ ).render( obj = cfg ).split( '\n' ):
                stream.write( line )
                if sys.platform.startswith( 'linux' ):
                    stream.write( '\n' )

        component = "import {{ {cls}Module }} from './{app}/{mod}.module';".format( cls = cfg.cls,
                                                                                    app = config.application,
                                                                                    mod = cfg.name )
        imports.append( component )

    appModule = {
        "files": [ "import { CustomMaterialModule } from './material.module';",
                   "import { GenCrudModule } from './common/gencrud.module';",
                   ],
        "imports": [ ],
        "declarations": [ "BrowserModule",
                          "BrowserAnimationsModule",
                          "HttpClientModule",
                          "FormsModule",
                          "ReactiveFormsModule",
                          "CustomMaterialModule",
                          "GenCrudModule" ],

        "entryComponents": [ ],
        "providers": [ ],
    }
    for imp in imports:
        if imp not in appModule[ 'files' ]:
            appModule[ 'files' ].append( imp )

    return appModule


def copyAngularCommon( source, destination ):
    files = os.listdir( source )
    for filename in files:
        if not os.path.isfile( os.path.join( destination, filename ) ) and \
               os.path.isfile( os.path.join( source, filename ) ):
            logger.debug( "Copy new file {0} => {1}".format( os.path.join( source, filename ),
                                                      os.path.join( destination, filename ) ) )
            shutil.copy( os.path.join( source, filename ),
                         os.path.join( destination, filename ) )

        elif os.path.isfile( os.path.join( destination, filename ) ):
            if sha256sum( os.path.join( destination, filename ) ) != sha256sum( os.path.join( source, filename ) ):
                # Hash differs, therefore replace the file
                logger.debug( "Hash differs, therefore replace the file {0} => {1}".format( os.path.join( source, filename ),
                                                                                     os.path.join( destination, filename ) ) )
                shutil.copy( os.path.join( source, filename ),
                             os.path.join( destination, filename ) )

            else:
                logger.debug( "{0} is the same {1}".format( os.path.join( source, filename ),
                                                     os.path.join( destination, filename ) ) )

        elif os.path.isdir( os.path.join( destination, filename ) ):
            copyAngularCommon( os.path.join( source, filename ), os.path.join( destination, filename ) )

    return