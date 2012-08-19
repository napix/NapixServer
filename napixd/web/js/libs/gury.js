/*
  gury.js - A jQuery inspired canvas utility library

  Copyright (c) 2010 Ryan Sandor Richards

  Permission is hereby granted, free of charge, to any person obtaining a copy
  of this software and associated documentation files (the "Software"), to deal
  in the Software without restriction, including without limitation the rights
  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
  copies of the Software, and to permit persons to whom the Software is
  furnished to do so, subject to the following conditions:

  The above copyright notice and this permission notice shall be included in
  all copies or substantial portions of the Software.

  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
  THE SOFTWARE.
*/

window.$g=window.Gury=function(e,t){function n(){for(var e=0;e<arguments.length;e++){var t=arguments[e];if(typeof t=="undefined"||t==null)return!1}return arguments.length>0}function r(e){return typeof e=="string"}function i(e){return typeof e=="object"}function s(e){return typeof e=="function"}function o(e){return i(e)||s(e)}function u(e){return i(e)&&n(e.getContext)}function a(e){return n(e.tagName)&&e.tagName=="IMG"}function l(){return f!=null}function h(e){if(c)throw"Gury: "+e}function d(){function i(e){return r(e)?e:(n(e._gury_hash)||(e._gury_hash=p++),e._gury_hash)}var e=this.table={},t=0;this.set=function(r,s){if(n(s)){var o=i(r);e[o]=s,t++}},this.has=function(t){var r=i(t);return n(e[r])},this.get=function(t){var n=i(t);return e[n]},this.remove=function(r){if(n(r)){var s=i(r);delete e[s],t--}},this.each=function(t){for(var n in e)t(e[n],n);return this},this.__defineGetter__("length",function(){return t})}function v(e){var t=this.table=new d,r=this.ordered=e?[]:!1;this.__defineGetter__("length",function(){return t.length}),this.has=function(e){return t.has(e)},this.add=function(e){return t.has(e)?this:(r&&r.push(e),t.set(e,e),this)},this.remove=function(e){if(!t.has(e))return null;if(r)for(var n=0;n<r.length;n++)if(r[n]==e){r.splice(n,1);break}return t.remove(e),e},this.each=function(e){if(r)for(var n=0;n<r.length;n++)e.call(this,r[n],n);else t.each(e);return this},this.clear=function(){return this.each(function(e,t){this.remove(e)}),this},this.sort=function(e){return n(r)&&r.sort(e),this},this.first=function(){return t.length<1||!n(r)?null:r[0]}}function m(){this.name=name,this._children={},this._objects=new v}function b(e){this.canvas=null,this.ctx=null,this._objects=new v(!0),this._tags=new m("__global"),this._transforms=new v(!0),this._paused=!1,this._loop_interval=null,this._clear_on_draw=!0,this._events={};var t=0;this.nextZ=function(){return t++}}function E(e,t){var s={};for(var o in s)n(t[o])||(t[o]=s[o]);var u=new b(t),a;if(r(e)){a=document.getElementById(e);if(!n(a))h('Unable to find canvas with id="'+e+'"');else if(y.has(a))return y.get(a);u.register(a)}else if(i(e)){a=e;if(y.has(a))return y.get(a);u.register(a)}else u.register(document.createElement("canvas"));return u}var f=t,c=!0,p=0;m.prototype=function(){var e=/^[a-zA-Z0-9_]+(\.[a-zA-Z0-9_]+)*$/;return{hasChild:function(e){return i(this._children[e])},addChild:function(e){return this._children[e]=new m(e)},getChild:function(e){return this._children[e]},getObjects:function(){return this._objects},find:function(t){if(!t.match(e))return null;var n=this,r=t.split("."),i=r[r.length-1];for(var s=0;s<r.length;s++){if(!n.hasChild(r[s]))return null;n=n.getChild(r[s])}return n},add:function(e,t){var n=e.split("."),r=this,i=n[n.length-1];for(var s=0;s<n.length;s++)r.hasChild(n[s])?r=r.getChild(n[s]):r=r.addChild(n[s]);return r._objects.add(t),t},clearObjects:function(){this._objects=new v},_remove_object:function(e){this._objects.remove(e);for(var t in this._children){var n=this._children[t];n._remove_object(e)}},remove:function(e){var t=new v;if(r(e)){var n=this.find(e);if(!n)return t;t=n.getObjects(),n.clearObjects()}else this._remove_object(e),t.add(e);return t}}}();var g=function(e,t){function l(e){var t=e.canvas;if(!n(t))return!1;var i=t.width,s=t.height;if(i!=a||s!=f)r.width=a=i,r.height=f=s;return u.clearRect(0,0,i,s),!0}function c(e,t){s(t)?ob.call(e,u,e.canvas):i(t)&&n(t.draw)&&t.draw(u,e.canvas)}function h(e,t){if(u==null)return!1;var n=u.getImageData(0,0,a,f),r=n.width,i=n.height,s=n.data;if(e<0||e>=r||t<0||t>=i)return!1;var o=r*4*t+e*4,l=n.data[o],c=n.data[o+1],h=n.data[o+2],p=n.data[o+3];return l>0||c>0||h>0||p>0}var r=document.createElement("canvas"),u=r.getContext("2d");e&&(r.style.position="absolute",r.style.top="10px",r.style.left="10px",r.style.background="white",document.body.appendChild(r));var a,f;return{hit:function(e,n,r,i){var s;t&&(s=(new Date).getTime());var u=!1;if(o(n)){if(!l(e))return!1;c(e,n),u=h(r,i)}return t&&console&&console.log&&console.log("Hit detection completed in "+((new Date).getTime()-s)+"ms"),u}}}(!1,!1),y=new d;b.prototype={register:function(e){return u(e)?(this.canvas=e,this.ctx=e.getContext("2d"),y.has(e)&&y.get(e).unregister(e),y.set(e,this),w.bind(this,e)):h("register() - Gury only supports registration of Canvas elements at this time."),this},unregister:function(e){return u(e)&&(y.remove(e),w.unbind(this,e),this.canvas=null,this.ctx=null),this},place:function(e){var t=this.canvas;return l()?f(e).append(t):typeof e=="object"&&typeof e.addChild=="function"?e.addChild(t):h("place() - Unable to place canvas tag (is jQuery loaded?)"),this},size:function(e,t){return this.canvas.width=e,this.canvas.height=t,this},background:function(e){return this.canvas.style.background=e,this},add:function(){var e=null,t;if(arguments.length<1)return this;if(arguments.length<2){t=arguments[0];if(!o(t))return this}else{e=arguments[0],t=arguments[1];if(!r(name)||!o(t))return this}e!=null&&this._tags.add(e,t);if(this._objects.has(t))return this;n(t._gury)||(t._gury={visible:!0,paused:!1,z:this.nextZ()}),this._objects.add(t);var i=["click","mousedown","mouseup","mousemove","mouseenter","mouseleave"];for(var u in i){var a=i[u];n(t[a])&&s(t[a])&&this.bind(t,a,t[a])}return this},addTransform:function(e){this._transforms.add(e)},removeTransform:function(e){this._transforms.remove(e)},remove:function(e){if(n(e)){var t=this,r=this._tags.remove(e);r.each(function(e){t._objects.remove(e),delete e._gury})}return this},clear:function(e){return typeof e!="undefined"?(this._clear_on_draw=e,this):(this.ctx.clearRect(0,0,this.canvas.width,this.canvas.height),this)},update:function(){var e=this;return e._objects.each(function(t){n(t.update)&&!t._gury.paused&&t.update(e)}),this},draw:function(){this._clear_on_draw&&this.clear();var e=this;return e._transforms.each(function(t){t.up(e.ctx,e.canvas)}),e._objects.each(function(t){if(!t._gury.visible||!o(t))return;typeof t=="function"?t.call(e,e.ctx,e.canvas):typeof t=="object"&&typeof t.draw!="undefined"&&t.draw(e.ctx,e.canvas)}),e._transforms.each(function(t){t.down(e.ctx,e.canvas)}),this},play:function(e){if(this._loop_interval!=null)return this;this.draw();var t=this;return this._loop_interval=setInterval(function(){t._paused||t.update().draw()},e),this},pause:function(){if(arguments.length>0){for(var e=0;e<arguments.length;e++){var t=arguments[e];r(t)?this.each(t,function(e){e._gury.paused=!e._gury.paused}):n(t._gury)&&(t._gury.paused=!t._gury.paused)}return this}return this._paused=!this._paused,this},stop:function(){return this._loop_interval!=null&&(clearInterval(this._loop_interval),this._paused=!1),this},each:function(){var e,t;if(arguments.length<2&&s(arguments[0]))t=arguments[0],this._objects.each(t);else if(r(arguments[0])&&s(arguments[1])){e=arguments[0],t=arguments[1];var n=this._tags.find(e);n&&n.getObjects().each(t)}else s(arguments[0])?(t=arguments[0],this._objects.each(t)):s(arguments[1])&&(t=arguments[1],this._objects.each(t));return this},hide:function(e){return this.each(e,function(e,t){e._gury.visible=!1})},show:function(e){return this.each(e,function(e,t){e._gury.visible=!0})},toggle:function(e){return this.each(e,function(e,t){e._gury.visible=!e._gury.visible})}};var w=function(){function e(e,t){var i=new v;if(r(t)){var s=e._tags.find(t);s!=null&&(i=s.getObjects())}else n(t)&&e._objects.has(t)&&i.add(t);return i}function t(e){return function(t,r){return n(t)&&(n(r)?this.bind(t,e,r):this.trigger(t,e)),this}}function i(e,t){var n=0,r=0;if(e.offsetParent)while(e)n+=e.offsetLeft,r+=e.offsetTop,e=e.offsetParent;return{x:t.pageX-n,y:t.pageY-r}}function s(e,t,r,s){if(n(e._events[r])){var o=i(t.canvas,t);t.canvasX=o.x,t.canvasY=o.y;var u=!1,a=new v(!0);e._events[r].each(function(e){a.add(e.target)}),a.sort(function(e,t){return e._gury.z<t._gury.z?1:-1}).each(function(n){!u&&g.hit(e,n,o.x,o.y)&&(u=!0,e.trigger(r,n,t),s&&s.call(n))}),!u&&s&&s.call(null)}}b.prototype.bind=function(t,r,i){if(n(t,r,i)){var s=this,o=s._events;e(s,t).each(function(e){n(o[r])||(o[r]=new d),o[r].has(e)||o[r].set(e,{target:e,handlers:[]}),o[r].get(e).handlers.push(i)})}return this},b.prototype.unbind=function(t,r,i){if(n(t,r)){var s=this,o=s._events;e(s,t).each(function(e){if(!n(o[r]))return;if(!o[r].has(e))return;if(n(i)){var t=o[r].get(e).handlers;for(var s=0;s<t.length;s++)if(t[s]==i){t.splice(s,1);break}}else o[r].remove(e)})}return this},b.prototype.trigger=function(e,t,r){if(n(e,this._events[e],t)&&this._events[e].has(t)){var i=this._events[e].get(t).handlers;for(var s=0;s<i.length;s++)i[s].call(t,r)}return this},b.prototype.click=t("click"),b.prototype.mousedown=t("mousedown"),b.prototype.mouseup=t("mouseup"),b.prototype.mousemove=t("mousemove"),b.prototype.mouseenter=t("mouseenter"),b.prototype.mouseleave=t("mouseleave");var o=null;return{bind:function(e,t){t.onclick=function(t){t.canvas=this,s(e,t,"click")},t.onmousedown=function(t){t.canvas=this,s(e,t,"mousedown")},t.onmouseup=function(t){t.canvas=this,s(e,t,"mouseup")},t.onmousemove=function(t){t.canvas=this,s(e,t,"mousemove",function(){this!=o&&(n(o)&&e.trigger("mouseleave",o,t),e.trigger("mouseenter",this),o=this)})},t.onmouseout=function(t){t.canvas=this,o!=null&&(e.trigger("mouseleave",o,t),o=null)}},unbind:function(e,t){t.onclick=null,t.onmousedown=null,t.onmouseup=null,t.onmousemove=null,t.onmouseleave=null}}}();return E.failWithException=function(e){return e?c=e?!0:!1:c},E}(window,window.jQuery)