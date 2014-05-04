var AnnotationToolAutocomplete = (function() {

    var $annotationFields = null;
    var labelCodes = null;


    return {

        init: function(params) {

            $annotationFields = params.$annotationFields;
            labelCodes = params.labelCodes;

            // Define a custom autocomplete widget.
            $.widget( 'ui.autocomplete', $.ui.autocomplete, {

                // Redefine _create(), copying 90% of it and just changing
                // a couple of handler initializations for our purposes.
                //
                // Yes, this massive code copying is far from ideal, but no
                // better solutions have come to mind.
                _create: function() {
                    // Some browsers only repeat keydown events, not keypress events,
                    // so we use the suppressKeyPress flag to determine if we've already
                    // handled the keydown event. #7269
                    // Unfortunately the code for & in keypress is the same as the up arrow,
                    // so we use the suppressKeyPressRepeat flag to avoid handling keypress
                    // events when we know the keydown event was used to modify the
                    // search term. #7799
                    var suppressKeyPress, suppressKeyPressRepeat, suppressInput,
                        nodeName = this.element[ 0 ].nodeName.toLowerCase(),
                        isTextarea = nodeName === "textarea",
                        isInput = nodeName === "input";

                    this.isMultiLine =
                        // Textareas are always multi-line
                        isTextarea ? true :
                            // Inputs are always single-line, even if inside a contentEditable element
                            // IE also treats inputs as contentEditable
                            isInput ? false :
                                // All other element types are determined by whether or not they're contentEditable
                                this.element.prop( "isContentEditable" );

                    this.valueMethod = this.element[ isTextarea || isInput ? "val" : "text" ];
                    this.isNewMenu = true;

                    this.element
                        .addClass( "ui-autocomplete-input" )
                        .attr( "autocomplete", "off" );

                    this._on( this.element, {
                        keydown: function( event ) {
                            if ( this.element.prop( "readOnly" ) ) {
                                suppressKeyPress = true;
                                suppressInput = true;
                                suppressKeyPressRepeat = true;
                                return;
                            }

                            suppressKeyPress = false;
                            suppressInput = false;
                            suppressKeyPressRepeat = false;
                            var keyCode = $.ui.keyCode;
                            var noKeyModifiers = !event.shiftKey && !event.ctrlKey
                                && !event.altKey && !event.metaKey;

                            switch ( event.keyCode ) {
                                case keyCode.PAGE_UP:
                                    suppressKeyPress = true;
                                    this._move( "previousPage", event );
                                    break;
                                case keyCode.PAGE_DOWN:
                                    suppressKeyPress = true;
                                    this._move( "nextPage", event );
                                    break;
                                case keyCode.UP:
                                    suppressKeyPress = true;
                                    // Changed to:
                                    // - only fire when the menu's visible
                                    // - only fire when no modifiers are pressed
                                    // - call stopPropagation() to prevent
                                    //   Mousetrap handler
                                    if ( this.menu.element.is( ":visible" )
                                       && noKeyModifiers ) {
                                        this._keyEvent( "previous", event );
                                        event.stopPropagation();
                                    }
                                    else {
                                        // This ensures that the autocomplete
                                        // choices are updated as we use
                                        // Ctrl+up/down to navigate the
                                        // label button grid.
                                        this._searchTimeout( event );
                                    }
                                    break;
                                case keyCode.DOWN:
                                    suppressKeyPress = true;
                                    // Same changes as keyCode.UP.
                                    if ( this.menu.element.is( ":visible" )
                                       && noKeyModifiers ) {
                                        this._keyEvent( "next", event );
                                        event.stopPropagation();
                                    }
                                    else {
                                        this._searchTimeout( event );
                                    }
                                    break;
                                case keyCode.ENTER:
                                    // when menu is open and has focus
                                    if ( this.menu.active ) {
                                        // #6055 - Opera still allows the keypress to occur
                                        // which causes forms to submit
                                        suppressKeyPress = true;
                                        event.preventDefault();
                                        this.menu.select( event );
                                    }
                                    break;
                                case keyCode.TAB:
                                    if ( this.menu.active ) {
                                        this.menu.select( event );
                                    }
                                    break;
                                case keyCode.ESCAPE:
                                    if ( this.menu.element.is( ":visible" ) ) {
                                        this._value( this.term );
                                        this.close( event );
                                        // Different browsers have different default behavior for escape
                                        // Single press can mean undo or clear
                                        // Double press in IE means clear the whole form
                                        event.preventDefault();
                                    }
                                    break;
                                default:
                                    suppressKeyPressRepeat = true;
                                    // search timeout should be triggered before the input value is changed
                                    this._searchTimeout( event );
                                    break;
                            }
                        },
                        keypress: function( event ) {
                            if ( suppressKeyPress ) {
                                suppressKeyPress = false;
                                if ( !this.isMultiLine || this.menu.element.is( ":visible" ) ) {
                                    event.preventDefault();
                                }
                                return;
                            }
                            if ( suppressKeyPressRepeat ) {
                                return;
                            }

                            // replicate some key handlers to allow them to repeat in Firefox and Opera
                            var keyCode = $.ui.keyCode;
                            var noKeyModifiers = !event.shiftKey && !event.ctrlKey
                                && !event.altKey && !event.metaKey;

                            switch ( event.keyCode ) {
                                case keyCode.PAGE_UP:
                                    this._move( "previousPage", event );
                                    break;
                                case keyCode.PAGE_DOWN:
                                    this._move( "nextPage", event );
                                    break;
                                case keyCode.UP:
                                    // Same changes as keydown.
                                    if ( this.menu.element.is( ":visible" )
                                       && noKeyModifiers ) {
                                        this._keyEvent( "previous", event );
                                        event.stopPropagation();
                                    }
                                    break;
                                case keyCode.DOWN:
                                    // Same changes as keydown.
                                    if ( this.menu.element.is( ":visible" )
                                       && noKeyModifiers ) {
                                        this._keyEvent( "next", event );
                                        event.stopPropagation();
                                    }
                                    break;
                            }
                        },
                        input: function( event ) {
                            if ( suppressInput ) {
                                suppressInput = false;
                                event.preventDefault();
                                return;
                            }
                            this._searchTimeout( event );
                        },
                        focus: function() {
                            this.selectedItem = null;
                            this.previous = this._value();
                        },
                        blur: function( event ) {
                            if ( this.cancelBlur ) {
                                delete this.cancelBlur;
                                return;
                            }

                            clearTimeout( this.searching );
                            this.close( event );
                            this._change( event );
                        }
                    });

                    this._initSource();

                    // Changed .menu( "instance" ); to .data( "ui-menu" );
                    // To prevent an error, as suggested here:
                    // http://forum.jquery.com/topic/issue-with-jquery-ui-selectmenu-no-such-method-instance
                    this.menu = $( "<ul>" )
                        .addClass( "ui-autocomplete ui-front" )
                        .appendTo( this._appendTo() )
                        .menu({
                            // disable ARIA support, the live region takes care of that
                            role: null
                        })
                        .hide()
                        .data( "ui-menu" );

                    this._on( this.menu.element, {
                        mousedown: function( event ) {
                            // prevent moving focus out of the text field
                            event.preventDefault();

                            // IE doesn't prevent moving focus even with event.preventDefault()
                            // so we set a flag to know when we should ignore the blur event
                            this.cancelBlur = true;
                            this._delay(function() {
                                delete this.cancelBlur;
                            });

                            // clicking on the scrollbar causes focus to shift to the body
                            // but we can't detect a mouseup or a click immediately afterward
                            // so we have to track the next mousedown and close the menu if
                            // the user clicks somewhere outside of the autocomplete
                            var menuElement = this.menu.element[ 0 ];
                            if ( !$( event.target ).closest( ".ui-menu-item" ).length ) {
                                this._delay(function() {
                                    var that = this;
                                    this.document.one( "mousedown", function( event ) {
                                        if ( event.target !== that.element[ 0 ] &&
                                            event.target !== menuElement &&
                                            !$.contains( menuElement, event.target ) ) {
                                            that.close();
                                        }
                                    });
                                });
                            }
                        },
                        menufocus: function( event, ui ) {
                            var label, item;
                            // support: Firefox
                            // Prevent accidental activation of menu items in Firefox (#7024 #9118)
                            if ( this.isNewMenu ) {
                                this.isNewMenu = false;
                                if ( event.originalEvent && /^mouse/.test( event.originalEvent.type ) ) {
                                    this.menu.blur();

                                    this.document.one( "mousemove", function() {
                                        $( event.target ).trigger( event.originalEvent );
                                    });

                                    return;
                                }
                            }

                            item = ui.item.data( "ui-autocomplete-item" );
                            if ( false !== this._trigger( "focus", event, { item: item } ) ) {
                                // use value to match what will end up in the input, if it was a key event
                                if ( event.originalEvent && /^key/.test( event.originalEvent.type ) ) {
                                    this._value( item.value );
                                }
                            }

                            // Announce the value in the liveRegion
                            label = ui.item.attr( "aria-label" ) || item.value;
                            if ( label && jQuery.trim( label ).length ) {
                                this.liveRegion.children().hide();
                                $( "<div>" ).text( label ).appendTo( this.liveRegion );
                            }
                        },
                        menuselect: function( event, ui ) {
                            var item = ui.item.data( "ui-autocomplete-item" ),
                                previous = this.previous;

                            // only trigger when focus was lost (click on menu)
                            if ( this.element[ 0 ] !== this.document[ 0 ].activeElement ) {
                                this.element.focus();
                                this.previous = previous;
                                // #6109 - IE triggers two focus events and the second
                                // is asynchronous, so we need to reset the previous
                                // term synchronously and asynchronously :-(
                                this._delay(function() {
                                    this.previous = previous;
                                    this.selectedItem = item;
                                });
                            }

                            if ( false !== this._trigger( "select", event, { item: item } ) ) {
                                this._value( item.value );
                            }
                            // reset the term after the select event
                            // this allows custom select handling to work properly
                            this.term = this._value();

                            this.close( event );
                            this.selectedItem = item;
                        }
                    });

                    this.liveRegion = $( "<span>", {
                        role: "status",
                        "aria-live": "assertive",
                        "aria-relevant": "additions"
                    })
                        .addClass( "ui-helper-hidden-accessible" )
                        .appendTo( this.document[ 0 ].body );

                    // turning off autocomplete prevents the browser from remembering the
                    // value when navigating through history, so we re-enable autocomplete
                    // if the page is unloaded before the widget is destroyed. #7790
                    this._on( this.window, {
                        beforeunload: function() {
                            this.element.removeAttr( "autocomplete" );
                        }
                    });
                }
            });


            // Bind autocomplete to the annotation fields.
            //
            // Note that the autocomplete bindings come AFTER our
            // hotkey bindings. This way, our hotkey bindings can
            // prevent autocomplete hotkeys from executing if they
            // want.
            //
            // TODO: Let autocomplete be an option.
            $annotationFields.autocomplete({
                // Auto-focus first option when menu is shown
                autoFocus: true,
                // delay in milliseconds between when a
                // keystroke occurs and when a search is performed
                delay: 0,
                // Get the label choices that start with what's typed so far
                source: function(request, response) {
                    var matches = [];
                    var i;
                    for (i = 0; i < labelCodes.length; i++) {
                        var codeLC = labelCodes[i].toLowerCase();
                        var termLC = request.term.toLowerCase();
                        if (codeLC.startsWith(termLC)) {
                            matches.push(labelCodes[i]);
                        }
                    }
                    matches.sort();
                    response(matches);
                }
            });
        }
    }
})();
