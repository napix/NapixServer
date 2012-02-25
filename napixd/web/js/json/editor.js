define( [
        'Backbone',
        'underscore',
        'jQuery',
        'json/viewer'
],function( Backbone, _, $, JSONView) {
        var NullEditView = Backbone.View.extend({
                tagName : 'em',
                dataType : 'null',
                initialize : function( value, originalValue) {
                    this.originalValue = originalValue;
                },
                render : function() {
                    this.$el.text( 'null' );
                    return this;
                },
                getValue : function() {
                    return null;
                }
            });
        var BooleanEditView = Backbone.View.extend({
                tagName: 'input',
                complex : false,
                dataType : 'boolean',
                initialize : function( value, originalValue) {
                    this.originalValue = originalValue;
                    this.$el
                    .prop( 'checked', value)
                    .prop('type', 'checkbox');
                },
                getValue : function() {
                    return this.$el.prop('checked');
                }
            });
        var StringEditView = Backbone.View.extend({
                tagName: 'input',
                complex : false,
                type : 'text',
                dataType : 'string',
                initialize : function( value, originalValue) {
                    this.originalValue = originalValue;
                    this.$el
                    .prop('type', this.type)
                    .prop( 'value', this._choose(value, originalValue))
                    .blur( _.bind( this.trigger, this, 'change'));
                },
                _choose : function(val, oval) {
                    var score = this._score( val);
                    var oscore = this._score( oval);
                    if ( !score && !oscore) {
                        return '';
                    }
                    val = score >= oscore ? val : oval;
                    return Math.max( score, oscore) > 0.25 ? val : _.first(val) ;
                },
                _score : function(val) {
                    if ( _.isString(val) )
                        return 1;
                    if ( _.isNumber(val) )
                        return 0.75;
                    if ( _.isNull(val) || _.isBoolean(val) || _.isEmpty(val) )
                        return 0;
                    if ( _.isArray(val))
                        return 0.25;
                    return 0.25;
                },
                getValue : function() { return this._getValue() ; },
                _getValue : function() {
                    return this.$el.prop('value');
                }
            });
        var NumberEditView = StringEditView.extend({
                type : 'number',
                dataType : 'number',
                getValue : function() {
                    return Number(this._getValue());
                },
                _score : function(val) {
                    if ( _.isNumber(val) )
                        return 1;
                    if ( _.isString(val) )
                        return 0.5;
                    return 0;
                }
            });
        var IterableEditView = Backbone.View.extend({
                complex : true,
                _choose : function(val, oval) {
                    var score = this._score( val);
                    var oscore = this._score( oval);
                    if ( !score && !oscore) {
                        return [];
                    }
                    val = score >= oscore ? val : oval;
                    return Math.max( score, oscore) == 0.25 ? [ val ] : val ;
                },
                _score : function(val) {
                    if ( _.isNull(val) || _.isBoolean(val) )
                        return 0;
                    if ( _.isNumber(val) || _.isString(val) )
                        return 0.25;
                    if ( _.isArray(val) )
                        return 0.75 + this.arrayBias * .25;
                    return 1 + this.arrayBias * .25;
                },
                render : function(value) {
                    _.each( this.valueViews, function( view) {
                            $('<li />')
                            .append( view.render().el )
                            .appendTo( this.el);
                        }, this);
                    if ( ! this.disableAddKey) {
                        $('<li />', {'text' : this.addText, 'class' : 'add-item' })
                        .click( this.addItem.bind(this) )
                        .appendTo( this.el);
                    }
                    return this;
                },
                removeKey : function( keyView) {
                    $( keyView.el ).parent( this.$el.children('li') ).remove();
                    this.valueViews = _.without( this.valueViews, keyView );
                },
                addItem : function() {
                    var emptyView = this.makeEmptyItem();
                    this.valueViews.push( emptyView);
                    $('<li />')
                    .append( emptyView.render().el )
                    .insertBefore(
                        this.$el.children('.add-item'));
                },
                makeEmptyItem : function() {
                    return JSONEditView.getView('');
                },
                disableAddKey : function() {
                    this.disabledAddKey = true;
                    return this;
                }
            });
        var ArrayEditView = IterableEditView.extend({
                tagName : 'ol',
                dataType : 'array',
                addText : 'Add a row',
                arrayBias : 1,
                initialize : function(values, originalValue) {
                    this.originalValue = originalValue;
                    values = this._choose( values, originalValue);
                    this.valueViews = _( values)
                    .chain()
                    .map(function( value) {
                            return JSONEditView.getView( value);
                        })
                    .map( function( view) {
                            view.bind( 'pop', this.removeKey, this);
                            return view;
                        }, this)
                    .value();
                },
                getValue : function() {
                    return _.map( this.valueViews, function(x) { return x.getValue() });
                }
            });

        var ObjectEditView = IterableEditView.extend({
                tagName : 'ul',
                dataType : 'object',
                addText : 'Add a key',
                arrayBias : 0,
                initialize : function( object, originalValue) {
                    this.originalValue = originalValue;
                    //console.log( object, originalValue, this._choose( object, originalValue))
                    object = this._choose( object, originalValue )
                    this.valueViews = _(object)
                    .chain()
                    .keys()
                    .map( function( key) {
                            return new ObjectKeyEditView( key, object[key]);
                        })
                    .map( function( view) {
                            view.bind( 'pop', this.removeKey, this);
                            return view;
                        }, this)
                    .value();
                },
                makeEmptyItem : function() {
                    return new ObjectKeyEditView('', '');
                },
                getValue : function() {
                    return _( this.valueViews)
                    .chain()
                    .map( function(x) { return x.getValue() })
                    .objectify()
                    .value();
                }
            });
        //*********************************** Edit Views ***************
          var KeyEditView = Backbone.View.extend({
                  tagName : 'label',
                  initialize : function(key){
                      this.editView = new StringEditView( key);
                      this.editView.bind( 'change', this.update.bind(this));
                  },
                  update : function() {
                      this.$el
                      .empty()
                      .text( this.editView.getValue() );
                  },
                  edit :  function() {
                      this.$el
                      .text('')
                      .append( this.editView.el )
                      .focus();
                  },
                  render : function() {
                      this.$el
                      .dblclick( this.edit.bind( this));
                      if ( this.editView.getValue() == ''){
                          this.edit();
                      }else {
                          this.update();
                      }
                      return this;
                  },
                  getValue : function() {
                      return this.editView.getValue();
                  }
              });
          var ObjectKeyEditView = Backbone.View.extend({
                  tagName : 'dd',
                  initialize : function( key, value) {
                      this.keyView = new KeyEditView(key);
                      this.valueView = JSONEditView.getView(value);
                      this.valueView.bind( 'pop', this.trigger.bind( this, 'pop', this));
                  },
                  render : function() {
                      this.$el
                      .append( $('<dl />')
                          .append( this.keyView.render().el )
                          .append(':'))
                      .append( $('<dt />').append( this.valueView.render().el  ))
                      return this;
                  },
                  getValue : function() {
                      return [ this.keyView.getValue(), this.valueView.getValue() ];
                  }
              });
          var MultiTypeEditView = Backbone.View.extend({
                  tagName : 'div',
                  initialize : function( options ) {
                      this.view = options.view ;
                  },
                  dataTypes : function() {
                      var y= _([
                              [ 'null','null', NullEditView ],
                              [ 'boolean', 'bool', BooleanEditView ],
                              [ 'number', '123', NumberEditView ],
                              [ 'string', 'abc', StringEditView ],
                              [ 'array', '[ ]', ArrayEditView ],
                              [ 'object', '{ }', ObjectEditView ],
                          ])
                      .chain()
                      .map( function(x) {
                              return [ _.first(x), _.rest(x) ]
                          })
                      .objectify()
                      .value();
                      return y
                  }(),
                  render: function() {
                      //this.el = $( this.view.complex ? '<div />' : '<span />', {'class' : 'json-mte'});

                      el = $('<div />', {'class' : 'json-mte btn-group'}).appendTo( this.el);
                      _.each( this.dataTypes, function( dataType, key) {
                              var span = $('<button />', { 'text' : dataType[0] , 'class' : 'btn btn-mini' })
                              .click( _.bind( this.transpose, this, dataType[1] ))
                              .appendTo( el);
                              if ( key == this.view.dataType) {
                                  span.addClass('selected');
                              }
                          }, this);

                      $('<button />', { 'text' : 'X', 'class' : 'btn btn-danger btn-mini' } )
                      .click( this.trigger.bind(this, 'pop', this))
                      .appendTo(el);

                      this.$el
                      .addClass(  'json-multiedit')
                      .append( this.view.render().el );
                      return this;
                  },
                  getValue : function() {
                      return this.view.getValue();
                  },
                  disableAddKey : function() {
                      this.view.complex && this.view.disableAddKey();
                      return this;
                  },
                  transpose : function( destDataType) {
                      this.view = new destDataType( this.view.getValue(), this.view.originalValue);
                      this.$el.empty();
                      this.render();
                  }
              });

          var JSONTextEditView = Backbone.View.extend({
                  tagName : 'textarea',
                  initialize : function( value) {
                      this.value = value
                  },
                  render : function() {
                      this.$el
                      .attr( 'value', JSON.stringify( this.value, null, 4))
                      return this;
                  },
                  getValue : function() {
                      return JSON.parse(this.el.value);
                  },
              });
          var JSONEditView = JSONView.extend({
                  className : 'json-edit json',
                  initialize : function( value, noAddKey) {
                      this.value = value;
                      this.view = null;
                      this.shown = '';
                      this.noAddKey = Boolean(noAddKey);
                  },
                  getValue : function() {
                      return this.view.getValue();
                  },
                  showText : function() {
                      if (this.shown  == 'text' ) return;
                      this.shown = 'text';
                      this.updateValue();
                      this.view = new JSONTextEditView( this.value);
                      this.updateView();
                  },
                  showBuilder : function() {
                      if (this.shown  == 'builder' ) return;
                      this.shown = 'builder';
                      this.updateValue();
                      this.view = JSONEditView.getView( this.value);
                      if (this.noAddKey) {
                          this.view.disableAddKey();
                      }
                      this.updateView();
                  },
                  updateValue : function() {
                      this.value = this.view ? this.view.getValue() : this.value;
                  },
                  updateView : function() {
                      this.$('.json-edit-body')
                      .empty()
                      .append( this.view.render().el );
                  },
                  render : function() {
                      this.$el
                      .append( $('<div />', {'class' : 'json-edit-header btn-group' ,
                                  'data-toggle' : 'buttons-radio'} )
                          .append(
                              $('<button />', { 'class': 'btn', 'text' : 'Text' })
                              .click( this.showText.bind(this) ))
                          .append(
                              $('<button />', { 'class': 'btn', 'text' : 'Builder'})
                              .button( 'toggle' )
                              .click( this.showBuilder.bind(this) )))
                      .append( $('<div />', {'class' : 'json-edit-body'} ))
                      .append(
                          $('<div />')
                          .append( $( '<input />', { 'value' : 'Valider' , 'class' : 'btn-primary'  }))
                          .click( this.validate.bind(this) ));
                      this.showBuilder();
                      return this;
                  },
                  validate : function() {
                      this.trigger( 'validate', this.getValue());
                  }
              }, {
                  getView : function( object) {
                      var view = JSONView._getView.call( this, object);
                      return new MultiTypeEditView({ 'view': new view(object, object) });
                  },
                  viewsMap : [
                      [ _.isBoolean, BooleanEditView ],
                      [ _.isNull, NullEditView ],
                      [ _.isArray, ArrayEditView ],
                      [ _.isNumber, NumberEditView ],
                      [ _.isString, StringEditView ],
                  ],
                  defaultView : ObjectEditView
              });
          return JSONEditView;
      });
