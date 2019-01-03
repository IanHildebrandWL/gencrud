import { Component, 
         Input, 
         forwardRef, 
         AfterViewInit, 
         OnChanges, 
         ViewEncapsulation, 
         OnInit} from '@angular/core';
import { NG_VALUE_ACCESSOR, 
         ControlValueAccessor, 
         FormGroupDirective} from '@angular/forms';
import { PytBaseComponent, CUSTOM_ANIMATIONS_CONTROLE } from './base.input.component';


export const CUSTOM_INPUT_CONTROL_VALUE_ACCESSOR: any = {
    provide: NG_VALUE_ACCESSOR,
    useExisting: forwardRef( () => PytTextInputComponent ),
    multi: true
};

@Component( {
    selector: 'pyt-text-input-box',
    template: `<div class="form">
    <mat-form-field color="accent">
        <input  matInput 
                class="custom-input__input" 
                id="{{ id }}"
                placeholder="{{ placeholder }}"
                [formControl]="control"/>
        <mat-icon matPrefix *ngIf="prefixType == 'icon'">{{ prefix }}</mat-icon>
        <mat-icon matSuffix *ngIf="suffixType == 'icon'">{{ suffix }}</mat-icon>
        <span matPrefix *ngIf="prefixType == 'text'">{{ prefix }}</span>
        <span matSuffix *ngIf="suffixType == 'text'">{{ suffix }}</span>
    </mat-form-field>
</div>`,
    styles: [   'custom-input__input{ width: 100%; }',
                'mat-form-field { width: 100%; }' ],
    encapsulation: ViewEncapsulation.None,
    providers: [ CUSTOM_INPUT_CONTROL_VALUE_ACCESSOR ],
    animations: CUSTOM_ANIMATIONS_CONTROLE
} )
export class PytTextInputComponent extends PytBaseComponent
                                   implements ControlValueAccessor, 
                                              AfterViewInit, 
                                              OnChanges, OnInit 
{
    constructor( formGroupDir: FormGroupDirective ) 
    {
        super( formGroupDir );
        return;
    }

}
