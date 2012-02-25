//depends : jQuery Backbone Credentials Server underscore objectify
//depends-js : models.js backbone.js jquery.js underscore.js underscoreextensions.js
//***************************** Selectors ************************

  define( [
          'underscore',
          'Backbone',
          'jQuery',
          'models/servers',
          'models/credentials'
  ] , function( _, Backbone, $, Servers, Credentials ) {
          var BaseItemView = Backbone.View.extend({
                  tagName : 'li',
                  initialize : function() {
                      this.model.bind('change', this.render, this);
                      this.model.bind('destroy', this.remove, this);

                      this.$el.click( this.model.select.bind(this.model) )
                  },
                  remove : function() {
                      this.$el.remove();
                  }
              });
          var BaseSelectorView = Backbone.View.extend({
                  initialize : function() {
                      this.setElement( $('#'+this.prefix));
                      this.collection.bind('add', this.addOne, this );
                      this.collection.bind('reset', this.addAll, this );

                      this.hidePrompt()

                      $('#'+this.prefix+'-plus').click(
                          this.showPrompt.bind(this) );
                      $('#'+this.prefix+'-prompt').keypress(
                          this.updateOnEnter.bind(this) );
                      this.collection.fetch();
                      this.bind( 'finished', this.hidePrompt, this);
                  },
                  addAll : function() {
                      this.collection.each( this.addOne, this );
                  },
                  addOne : function(item) {
                      item.bind('selected', this.select );
                      this.$('#'+this.prefix+'-body').append(
                          new this.ItemView({ model : item }).render().el );
                  },
                  hidePrompt : function() {
                      this.$('#'+this.prefix+'-prompt').hide();
                      this.$('#'+this.prefix+'-plus').show();
                  },
                  showPrompt : function(){
                      this.$('#'+this.prefix+'-prompt')
                      .show()
                      .first()
                      .find('input')
                      .attr('value','')
                      .focus();
                      this.$('#'+this.prefix+'-plus').hide();
                  },
                  updateOnEnter : function(e) {
                      if (e.keyCode  == 13 ) { //Enter
                          this.addItem();
                      } else if (e.keyCode == 27) {
                          this.trigger( 'finished');
                      }
                  },
                  addItem : function() {
                      var obj = _( this.$('input').toArray())
                      .chain()
                      .map( function(x) { return $(x) })
                      .map( function(x) { return [ x.prop('name') , x.prop('value') ] })
                      .objectify()
                      .value();
                      var y = this.collection.create( obj );
                      if (y) {
                          this.trigger( 'finished');
                          y.select();
                      }
                  }
              });
          //************ Server Selector ***********
          var ServerItemView = BaseItemView.extend({
                  render : function() {
                      this.$el
                      .text( this.model.get('host') )
                      .toggleClass('selected', this.model.get('selected'));
                      return this;
                  }
              });
          var ServerSelectorView = BaseSelectorView.extend({
                  collection : Servers,
                  ItemView : ServerItemView,
                  prefix : 'connections-servers'
              });

          //************ Login Selector ***********
          var LoginItemView = BaseItemView.extend({
                  render : function() {
                      this.$el
                      .text( this.model.get('login') )
                      .toggleClass('selected', this.model.get('selected'));
                      return this;
                  }
              });
          var LoginSelectorView = BaseSelectorView.extend({
                  collection : Credentials,
                  ItemView : LoginItemView,
                  prefix : 'connections-credentials'
              });


          //************ Selectors ***********
          var SelectorsView = Backbone.View.extend({
                  initialize : function() {
                      this.serverSelector = new ServerSelectorView();
                      this.loginSelector = new LoginSelectorView();
                  }
              });
          return SelectorsView;
      });
