define( [
        'Backbone',
        'underscore',
        'jQuery'
    ], function( Backbone, _, $) {
        var SimpleView = Backbone.View.extend({
                tagName : 'span',
                className : 'json-simple',
                viewName : 'simple',
                complex : false,
                initialize : function(value) {
                    this.value = String(value);
                },
                render : function() {
                    this.$el
                    .text( this.value);
                    return this;
                }
            });
        var EmptyView = SimpleView.extend({
                viewName : 'empty',
                initialize : function(value) {
                    this.value = '?'
                    _.any( [
                            [_.isNull , 'null'],
                            [_.isString , 'Empty String'],
                            [_.isArray , 'Empty Array'],
                            [_.bind( _.identity, _, true) , 'Empty Object']
                        ], function(x) {
                            if(x[0](value)) {
                                this.value = x[1];
                                return true;
                            }
                            return false;
                        } , this);
                }
            });
        var ArrayView = Backbone.View.extend({
                tagName : 'ol',
                viewName : 'array',
                complex : true,
                initialize : function( value) {
                    this.listViews = _.map( value, JSONView.getView, JSONView);
                },
                render : function() {
                    _.each( this.listViews, function( view) {
                            $('<li />')
                            .append( view.render().el)
                            .appendTo( this.el);
                        }, this);
                    return this;
                }
            });
        var KeyView =  Backbone.View.extend({
                viewName : 'key',
                complex : false,
                tagName : 'li',
                initialize : function( key, value) {
                    this.key = key;
                    this.valueView = JSONView.getView( value);
                },
                render : function() {
                    if ( this.valueView.complex ) {
                        $('<dd />')
                        .append( $('<dl />', { 'class' : 'json-key', 'text' : this.key }))
                        .append( $( '<dt />')
                            .append( this.valueView.render().el) )
                        .appendTo( this.el);
                    } else {
                        $('<div />')
                        .append( $('<span />', { 'class' : 'json-key', 'text' : this.key}) )
                        .append( ' ')
                        .append( this.valueView.render().el)
                        .appendTo( this.el);
                    }
                    return this;
                },
            });
        var ObjectView = Backbone.View.extend({
                tagName : 'ul',
                viewName : 'object',
                complex : true,
                initialize : function(object) {
                    this.keyViews = _.map( _.keys(object), function( key) {
                            return new KeyView( key, object[key] )
                        });
                },
                render : function() {
                    _.each( this.keyViews, function( view) {
                            this.$el.append( view.render().el );
                        }, this);
                    return this;
                }
            });
        var JSONView = Backbone.View.extend({
                className : 'json-object json',
                tagName : 'div',
                initialize : function(value) {
                    this.inside = this.constructor.getView( value);
                },
                render : function() {
                    this.$el.append( this.inside.render().el);
                    return this;
                }
            }, {
                _getView : function( value) {
                    for( x in this.viewsMap) {
                        if (this.viewsMap[x][0]( value) ) {
                            return this.viewsMap[x][1];
                        }
                    }
                    return this.defaultView;
                },
                getView : function( value) {
                    var view = this._getView(value);
                    return new view(value);
                },
                viewsMap : [
                    [ _.isBoolean, SimpleView ],
                    [ _.isNumber, SimpleView ],
                    [ _.isNull, EmptyView ],
                    [ _.isEmpty, EmptyView ],
                    [ _.isString, SimpleView ],
                    [ _.isArray, ArrayView ],
                ],
                defaultView :ObjectView
            });
        return JSONView;
    });
