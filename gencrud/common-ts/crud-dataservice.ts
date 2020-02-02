/*
#
#   Python backend and Angular frontend code generation by gencrud
#   Copyright (C) 2018-2020 Marc Bertens-Nguyen m.bertens@pe2mbs.nl
#
#   This library is free software; you can redistribute it and/or modify
#   it under the terms of the GNU Library General Public License GPL-2.0-only
#   as published by the Free Software Foundation.
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
*/
import { BehaviorSubject, Observable } from 'rxjs';
import { HttpClient, HttpErrorResponse, HttpParams } from '@angular/common/http';


export interface PytSelectList
{
    value:  any;
    label:  string;
}


export class CrudDataService<T> 
{
    protected debug: boolean = false;
    protected _uri: string;
    protected _backend_filter: string = null;
    dataChange: BehaviorSubject<T[]> = new BehaviorSubject<T[]>([]);
    // Temporarily stores data from dialogs
    dialogData: T;

    constructor ( protected httpClient: HttpClient ) 
    {
        return;
    }

    public get uri() : string
    {
      return this._uri;
    }

    public set uri( value: string )
    {
      this._uri = value;
      return;
    }

    public get data(): T[] 
    {
        return this.dataChange.value;
    }

    public getDialogData() 
    {
        return this.dialogData;
    }

    /** CRUD METHODS */
    public getAll( _backend_filter: any ): void
    {
        let uri = '/list'
        if ( _backend_filter !== null )
        {
            this._backend_filter = _backend_filter;
            uri += '/' + _backend_filter.id + '/' + _backend_filter.value
        }
        this.httpClient.get<T[]>( this._uri + uri ).subscribe(
            data => {
                this.dataChange.next( data );
            },
            (error: HttpErrorResponse) => {
                console.log (error.name + ' ' + error.message);
            }
        );
        return;
    }

    public getSelectList( value: string, label: string ): Observable<PytSelectList[]>
    {
        const params = new HttpParams().set('label', label ).set('value', value );
        return ( Observable.create( observer => {
            this.httpClient.get<PytSelectList[]>( this._uri + '/select', { params: params } )
            .subscribe( ( data ) => {
                    if ( this.debug )
                    {
                        console.log( 'getSelectList() => ', data );
                    }
                    observer.next( data );
                    observer.complete();
                },
                ( error: HttpErrorResponse ) => {
                    console.log (error.name + ' ' + error.message);
                }
            );
        } ) );
    }

    public getSelectionList( value: string, label: string ): Observable<Array<string>>
    {
        const params = new HttpParams().set('label', label ).set('value', value );
        return ( Observable.create( observer => {
            this.httpClient.get<PytSelectList[]>( this._uri + '/select', { params: params } )
            .subscribe( ( data ) => {
                    if ( this.debug )
                    {
                        console.log( 'getSelectList() => ', data );
                    }
                    let result = new Array<string>();
                    result.push( '-' );
                    data = data.sort( ( n1, n2 ) => {
                        if (n1.value > n2.value )
                        {
                            return 1;
                        }
                        else if (n1.value < n2.value )
                        {
                            return -1;
                        }
                        return 0;
                    });
                    for ( let entry of data )
                    {
                        result.push( entry.label );
                    }
                    observer.next( result );
                    observer.complete();
                },
                ( error: HttpErrorResponse ) => {
                    console.log (error.name + ' ' + error.message);
                }
            );
        } ) );
    }

    public lockRecord( record: T ): void 
    {
        this.dialogData = record;
        this.httpClient.post<T>( this._uri + '/lock', record ).subscribe(result => {
            if ( this.debug )
            {
                console.log( result );
            }
        },
        (error: HttpErrorResponse) => {
            console.log( error.name + ' ' + error.message );
        });
        return;
    }

    public unlockRecord( record: T ): void 
    {
        this.dialogData = null;
        this.httpClient.post<T>( this._uri + '/unlock', record ).subscribe(result => {
            if ( this.debug )
            {
                console.log( result );
            }
        },
        (error: HttpErrorResponse) => {
            console.log( error.name + ' ' + error.message );
        });
        return;
    }

    public addRecord( record: T ): void
    {
        if ( this.debug )
        {
            console.log( 'addRecord', record );
        }
        this.dialogData = record;
        this.httpClient.post<T>( this._uri + '/new', record ).subscribe(result => {
            if ( this.debug )
            {
                console.log( result );
            }
            this.getAll( this._backend_filter );
        },
        (error: HttpErrorResponse) => {
            console.log( error.name + ' ' + error.message );
        });
        return;
    }

    public getRecordById( id )
    {
        if ( this.debug )
        {
            console.log( 'getRecordById', id );
        }
        return this.httpClient.get<T>( this._uri + '/get/' + id );
    }

    public getRecord( record: T ): void 
    {
        if ( this.debug )
        {
            console.log( 'getRecord', record );
        }
        this.dialogData = record;
        this.httpClient.get<T>( this._uri + '/get', record ).subscribe(result => {
            if ( this.debug )
            {
                console.log( result );
            }
        },
        (error: HttpErrorResponse) => {
            console.log( error.name + ' ' + error.message );
        });
        return;
    }

    public updateRecord( record: T ): void 
    {
        if ( this.debug )
        {
            console.log( 'updateRecord.orignal ', this.dialogData );
            console.log( 'updateRecord.updated ', record );
        }
        for ( let key of Object.keys( record ) )
        {
            if ( this.debug )
            {
                console.log( 'update key ' + key + ' with value ', record[ key ] );
            }
            this.dialogData[ key ] = record[ key ];
        }
        this.httpClient.post<T>( this._uri + '/update', this.dialogData ).subscribe( result => {
            if ( this.debug )
            {
                console.log ( result );
            }
        },
        (error: HttpErrorResponse) => {
            console.log( error.name + ' ' + error.message );
        });
        return;
    }

    public deleteRecord( record: string ): void 
    {
        console.log( 'deleteRecord', record );
        this.httpClient.delete<T>( this._uri + '/' + record ).subscribe( result => {
            if ( this.debug )
            {
                console.log ( result );
            }
        },
        (error: HttpErrorResponse) => {
            console.log ( error.name + ' ' + error.message );
        });
        return;
    }

    public genericPut( uri: string, params: any ): void
    {
        console.log( 'genericPut', uri, params );
        this.httpClient.put( this._uri + uri, params ).subscribe( result => {
            if ( this.debug )
            {
                console.log ( result );
            }
        },
        (error: HttpErrorResponse) => {
            console.log ( error.name + ' ' + error.message );
        });
        return;
    }

    public genericGet( uri: string, params: any ): Observable<any>
    {
        console.log( 'genericGet', uri, params );
        return this.httpClient.get( this._uri + uri, params );
    }
}
