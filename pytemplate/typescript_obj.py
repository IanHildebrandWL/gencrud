import json
import unittest

class TypeScript( object ):
    def __init__( self ):
        self.__indent = 0
        self.__line = 1
        self.__column = 1
        return

    def _buildDict( self, obj, indent ):
        result = '{'
        if self.__indent > 0:
            result += '\n'
            indent += self.__indent
        else:
            result += ' '

        items = []
        for key in sorted( obj.keys() ):
            value = obj[ key ]
            items.append( "{ind}{key}: {val}".format( ind = ' ' * indent,
                                                            key = key,
                                                            val = self._build( value, indent ) ) )

        joinStr = ', '
        if self.__indent > 0:
            joinStr = ',\n'.format( ' ' * indent )

        result += joinStr.join( items )

        if self.__indent > 0:
            result += '\n'
            indent -= self.__indent

        else:
            indent = 1

        result += '{0}}}'.format( ' ' * indent )

        return result

    def _buildArray( self, obj, indent ):
        result = '['
        if self.__indent > 0:
            result += '\n'
            indent += self.__indent
        else:
            result += ' '

        if self.__indent > 0:
            result += ',\n'.join( [ '{0}{1}'.format( ' ' * indent, self._build( x, indent ) ) for x in obj ] )

        else:
            result += ', '.join( [ '{0}'.format( self._build( x, indent ) ) for x in obj ] )

        if self.__indent > 0:
            indent -= self.__indent
            result += '\n'
        else:
            indent = 1

        return result + '{0}]'.format( ' ' * indent )

    def _build( self, obj, indent = 0 ):
        typeObj = type( obj )
        if typeObj is dict:
            return self._buildDict( obj, indent )

        elif typeObj in ( tuple, list ):
            return self._buildArray( obj, indent )

        else:
            return obj

        return

    def build( self, obj, indent = 0 ):
        typeObj = type( obj )
        self.__indent = indent
        if type( obj ) in ( dict, tuple, list ):
            return self._build( obj )

        raise Exception( 'invalid starting data type for {}'.format( repr( obj ) ) )

    def __skipWhiteSpace( self, text, idx ):
        while idx < len( text ) and text[ idx ] in ( ' ', '\t', '\n', '\r' ):
            if text[ idx ] == '\n':
                self.__line += 1
                self.__column = 1

            idx += 1

        return idx

    def _parseDict( self, text, idx ):
        result = {}
        idx = self.__skipWhiteSpace( text, idx )
        while idx < len( text ) and text[ idx ] != '}':
            idx = self.__skipWhiteSpace( text, idx )
            key, idx = self._parse( text, idx )
            idx = self.__skipWhiteSpace( text, idx )
            if text[ idx ] == ':':
                idx += 1
                self.__column += 1
                result[ key ], idx = self._parse( text, idx )
                if text[ idx ] == '}':
                    continue

                idx += 1
                self.__column += 1
            elif text[ idx ] == '}':
                break

            elif text[ idx ] == ',':
                # next element
                print( 'next element: {}'.format( key ) )
                raise Exception( 'format error: found {}'.format( text[ idx ] ) )

            else:
                # format errror
                raise Exception( 'format error: found {}'.format( text[ idx ] ) )

        idx += 1
        self.__column += 1
        return result, idx


    def _parseArray( self, text, idx ):
        result = []
        idx = self.__skipWhiteSpace( text, idx )
        while idx < len( text ) and text[ idx ] != ']':
            item, idx = self._parse( text, idx )
            result.append( item )
            if text[ idx ] == ']':
                continue

            idx += 1
            self.__column += 1
            idx = self.__skipWhiteSpace( text, idx )

        idx += 1
        self.__column += 1
        return result, idx

    def _parse( self, text, idx ):
        idx = self.__skipWhiteSpace( text, idx )
        if text[ idx ] == '{':
            # dict
            idx += 1
            self.__column += 1
            obj, idx = self._parseDict( text, idx )

        elif text[ idx ] == '[':
            # array
            idx += 1
            self.__column += 1
            obj, idx = self._parseArray( text, idx )

        else:
            obj = ''
            while idx < len( text ) and text[ idx ] not in ',{}[]: \t\n\r':
                obj += text[ idx ]
                self.__column += 1
                idx += 1

        return ( obj, idx )

    def parse( self, text ):
        self.__line = 1
        self.__column = 1
        try:
            if type( text ) in ( tuple, list ):
                return self._parse( '\n'.join( text ), 0 )[ 0 ]

            return self._parse( text, 0 )[ 0 ]

        except Exception:
            print( text )
            raise


class MyTest( unittest.TestCase ):
    TEST_DATA = {
        "test": "testing",
        "hello": {
            "key": "value",
            "sub": "2nd"
        },
        "array": [
            "Item-1",
            {   "Item-2": "2",
                "mark": "true"
            }
        ]
    }
    #
    #   Note that this block is in a sorted order,
    #   as the generate function will sort keys in the dictionaries
    #
    OUTPUT = '''{
  array: [
    Item-1,
    {
      Item-2: 2,
      mark: true
    }
  ],
  hello: {
    key: value,
    sub: 2nd
  },
  test: testing
}'''
    OUTPUT_FLAT = '{ array: [ Item-1, { Item-2: 2, mark: true } ], hello: { key: value, sub: 2nd }, test: testing }'

    def setUp( self ):
        self.ts = TypeScript()
        return

    def tearDown(self):
        self.ts = None
        return

    def testGenerateTsCodeFlat( self ):
        data = self.ts.build( self.TEST_DATA )
        self.assertEqual( data,
                          self.OUTPUT_FLAT,
                          'Generated data not correct' )
        return

    def testGenerateTsCode( self ):
        self.assertEqual( self.ts.build( self.TEST_DATA, 2 ),
                          self.OUTPUT,
                          'Generated data not correct' )
        return

    def testParseTsCode( self ):
        self.assertEqual( json.dumps( self.ts.parse( self.OUTPUT ), sort_keys = True ),
                          json.dumps( self.TEST_DATA, sort_keys = True ),
                          'Parsed data not correct' )
        return


if __name__ == '__main__':
    unittest.main()
