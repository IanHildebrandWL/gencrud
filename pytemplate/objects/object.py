#
#   Python backend and Angular frontend code generation by gencrud
#   Copyright (C) 2018 Marc Bertens-Nguyen m.bertens@pe2mbs.nl
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
#   Frontend view for the ${ obj.name } table, this is generated by the
#   gencrud.py module. When modifing the file make sure that you remove
#   the table from the configuration.
#
from pytemplate.objects.menuitem import TemplateMenuItem
from pytemplate.objects.table import TemplateTable
from pytemplate.objects.actions.actions import TemplateActions
from pytemplate.util.exceptions import InvalidSetting


class TemplateObject( object ):
    def __init__( self, parent, **cfg ):
        self.__config       = cfg
        self.__parent       = parent
        self.__columns      = []
        self.__primaryKey   = ''
        self.__title        = None
        if 'menu' in cfg:
            self.__menuRoot = TemplateMenuItem( 'menu', **cfg )

        else:
            self.__menuRoot = None

        if 'menuItem' in cfg:
            self.__menuItem = TemplateMenuItem( 'menuItem', **cfg )

        else:
            self.__menuItem = None

        self.__actionWidth  = '5%'
        if 'action-width' in cfg:
            self.__actionWidth = cfg[ 'action-width' ]

        self.__actions      = TemplateActions( self,
                                               self.name,
                                               self.__config.get( 'actions', [] ) )
        self.__table        = TemplateTable( **self.__config.get( 'table', {} ) )
        return

    @property
    def title( self ):
        return self.__config.get( 'title', self.__config.get( 'class', '<-Unknown->' ) )

    @property
    def application( self ):
        return self.__config.get( 'application', self.__parent.application )

    @property
    def name( self ):
        return self.__config.get( 'name', '' )

    @property
    def cls( self ):
        return self.__config.get( 'class', '' )

    @property
    def uri( self ):
        return self.__config.get( 'uri', '' )

    @property
    def actions( self ):
        return self.__actions

    @property
    def menu( self ):
        return self.__menuRoot

    @property
    def menuItem( self ):
        return self.__menuItem

    @property
    def table( self ):
        return self.__table

    @property
    def actionWidth( self ):
        return self.__actionWidth

    def orderBy( self ):
        orderList = []
        for field in self.__table.orderBy:
            orderList.append( 'order_by( {}.{} )'.format( self.cls, field ) )

        return '.'.join( orderList )

    @property
    def externalService( self ):
        FILLER = '                 , '
        FILLER_LF = '\r\n                 , '
        result = []
        for field in self.__table.columns:
            if field.ui is not None:
                if field.ui.isCombobox() or field.ui.isChoice():
                    if field.ui.service is not None:
                        result.append( 'public {name}Service: {cls}'.format(
                                        name = field.ui.service.name,
                                        cls = field.ui.service.cls ) )
                    elif field.ui.hasResolveList():
                        pass

                    else:
                        raise Exception( "service missing in {} in field {}".format( self.__table.name, field.name )  )

        return ( FILLER if len( result ) > 0 else '' ) + ( FILLER_LF.join( result ) )

