define(["Backbone","underscore","jQuery","libs/mustache","views/json/viewer","views/json/editor","napixclient"],function(e,t,n,r,i,s,o){var u=e.View.extend({tagName:"em",render:function(){return this.$el.text("empty"),this}}),a=e.View.extend({id:"",emptyView:u,initialize:function(){this.setElement(n("#"+this.id)),this.shown=!1,this.rendered=!1,this.view=new this.emptyView,n("#"+this.id+"-label").bind("shown",this.show.bind(this)).bind("hidden",this.hide.bind(this))},gotObject:function(e,t){return this.rendered=!1,this.view=e?new this.insideView(e,t):new this.emptyView,this.render()},render:function(){return!this.rendered&&this.shown&&(this.rendered=!0,this.actuallyRender()),this},actuallyRender:function(){this.$el.empty().append(this.view.render().el),this.trigger("rendered",this.view)},available:function(e){n("#"+this.id+"-label").toggle(Boolean(e)),e||(this.shown=!1)},hide:function(){return this.shown=!1,this},show:function(){return this.shown=!0,this.render(),this}}),f=e.View.extend({className:"accordion-group",events:{"click .view":"click","click .download":"downloadClick"},template:r.compile('<div class="accordion-heading"><div class="view accordion-toggle" title="{{doc}}" data-view="{{format}}" data-toggle="collapse" data-target="#explorer-format-{{format}}" >Format: {{format}}<i class="icon-download download" /></div></div><div id="explorer-format-{{format}}" class="accordion-body collapse"><div class="accordion-inner"></div></div>'),initialize:function(e){this.path=e.path,this.format=e.format,this.doc=e.doc},render:function(){return this.$el.append(this.template(this)),this},click:function(){if(t.isUndefined(this.url))this.getFormat();else{if(this.url===null)return!1;if(!!this.displayable)return!0;this.download()}return!1},getFormat:function(e){this.url=null,o.request({blob:!0,method:"GET",uri:this.path+"?format="+this.format,success:t.bind(this.gotFormat,this),fail:t.bind(this.failed,this)})},failed:function(){this.url=undefined},gotFormat:function(e,t,r){this.blob=e;var s=this.url=window.URL.createObjectURL(e),o=this.$(".accordion-inner"),u,a=r.getResponseHeader("Content-type")||"",f=a.indexOf("text")===0||a==="application/xml";this.displayable=!0;if(a.indexOf("image")===0)n("<img />",{src:s,alt:t.uri}).appendTo(o);else if(a==="application/json")u=new FileReader,u.onloadend=function(){o.append((new i(JSON.parse(this.result))).render().el)},u.readAsText(e);else if(f){var l=n("<pre />").appendTo(o);u=new FileReader,u.onloadend=function(){l.text(this.result)},u.readAsText(e)}else this.download(),this.displayable=!1;this.displayable&&this.$(".accordion-body").collapse("show"),this.trigger("gotFormat",s,e)},downloadClick:function(){return this.url?this.download():(this.bind("gotFormat",this.download,this),t.isUndefined(this.url)&&this.getFormat()),!1},download:function(){location=this.url}}),l=a.extend({id:"explorer-object",insideView:i,events:{"click button":"buttonClicked"},gotObject:function(e,n){return this.path=n.path,this.actions=n.actions,this.formatViews=t.map(n.views,function(e,t){return new f({format:t,doc:e,path:this.path})},this),this.deletable=n.deletable,this.editable=n.editable,l.__super__.gotObject.call(this,e,n),this},buttonClicked:function(e){this.trigger(e.target.dataset.event,this.path,e.target.dataset.action)},template:r.compile('<div id="explorer-object-actions" class="btn-group" >{{#deletable}}<button class="btn btn-danger" data-event="delete" >Delete</button>{{/deletable}}{{#editable}}<button class="btn" data-event="edit" >Edit</button>{{/editable}}{{#actions}}<button class="btn" data-event="action" title="{{val}}"  data-action="{{key}}" >{{key}}</button>{{/actions}}</div>'),actuallyRender:function(){l.__super__.actuallyRender.call(this),this.$el.append(this.template({deletable:this.deletable,editable:this.editable,actions:t.items(this.actions)})),t.each(this.formatViews,function(e){this.$el.append(e.render().el)},this)}}),c=a.extend({id:"explorer-help",insideView:i}),h=a.extend({insideView:s.FixedView,initialize:function(){h.__super__.initialize.call(this),this.bind("rendered",this.onRender,this)},gotObject:function(e,t){this.path=t.path,h.__super__.gotObject.call(this,e,t)},onRender:function(e){e.bind("validate",t.bind(this.trigger,this,"validate",this.path))}}),p=h.extend({id:"explorer-edit"}),d=e.View.extend({initialize:function(e,t){this.collectionPath=e,this.types=t.types},render:function(){return o.getNewObject(this.collectionPath,this.gotTemplate.bind(this)),this},gotTemplate:function(e){var n=new s.FixedView(e,this.types);this.$el.append(n.render().el),this.$(":input").not(".btn").first().focus(),n.bind("validate",t.bind(this.trigger,this,"validate"))}}),v=h.extend({id:"explorer-create",insideView:d,gotObject:function(e,n){n.types=t.chain(n.resourceFields).map(function(e,t){return[t,e.type||"null"]}).objectify().value(),v.__super__.gotObject.call(this,e,n)}});return{HelpView:c,EditView:p,CreateView:v,ObjectView:l}})