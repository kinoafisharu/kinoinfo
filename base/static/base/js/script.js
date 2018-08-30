/*!
 * jQuery Cookie Plugin v1.3.1
 * https://github.com/carhartl/jquery-cookie
 * Copyright 2013 Klaus Hartl
 * Released under the MIT license
 */
(function (factory) {
	if (typeof define === 'function' && define.amd) {
		define(['jquery'], factory);
	} else {
		factory(jQuery);
	}
}(function ($) {
	var pluses = /\+/g;
	function raw(s) {
		return s;
	}
	function decoded(s) {
		return decodeURIComponent(s.replace(pluses, ' '));
	}
	function converted(s) {
		if (s.indexOf('"') === 0) {
			s = s.slice(1, -1).replace(/\\"/g, '"').replace(/\\\\/g, '\\');
		}
		try {
			return config.json ? JSON.parse(s) : s;
		} catch(er) {}
	}
	var config = $.cookie = function (key, value, options) {
		if (value !== undefined) {
			options = $.extend({}, config.defaults, options);
			if (typeof options.expires === 'number') {
				var days = options.expires, t = options.expires = new Date();
				t.setDate(t.getDate() + days);
			}
			value = config.json ? JSON.stringify(value) : String(value);

			return (document.cookie = [
				config.raw ? key : encodeURIComponent(key),
				'=',
				config.raw ? value : encodeURIComponent(value),
				options.expires ? '; expires=' + options.expires.toUTCString() : '',
				options.path    ? '; path=' + options.path : '',
				options.domain  ? '; domain=' + options.domain : '',
				options.secure  ? '; secure' : ''
			].join(''));
		}
		var decode = config.raw ? raw : decoded;
		var cookies = document.cookie.split('; ');
		var result = key ? undefined : {};
		for (var i = 0, l = cookies.length; i < l; i++) {
			var parts = cookies[i].split('=');
			var name = decode(parts.shift());
			var cookie = decode(parts.join('='));
			if (key && key === name) {
				result = converted(cookie);
				break;
			}
			if (!key) {
				result[name] = converted(cookie);
			}
		}
		return result;
	};
	config.defaults = {};
	$.removeCookie = function (key, options) {
		if ($.cookie(key) !== undefined) {
			$.cookie(key, '', $.extend({}, options, { expires: -1 }));
			return true;
		}
		return false;
	};
}));
/*
 * jQuery MultiSelect UI Widget 1.13
 * Copyright (c) 2012 Eric Hynds
 * http://www.erichynds.com/jquery/jquery-ui-multiselect-widget/
 * Dual licensed under the MIT and GPL licenses:
 */
(function(d){var k=0;d.widget("ech.multiselect",{options:{header:!0,height:175,minWidth:225,classes:"",checkAllText:"Выбрать все",uncheckAllText:"Убрать все",noneSelectedText:"БУДУТ ВЫБРАНЫ ВСЕ",selectedText:"# выбрано",selectedList:0,show:null,hide:null,autoOpen:!1,multiple:!0,position:{}},_create:function(){var a=this.element.hide(),b=this.options;this.speed=d.fx.speeds._default;this._isOpen=!1;a=(this.button=d('<button type="button"><span class="ui-icon ui-icon-triangle-2-n-s"></span></button>')).addClass("ui-multiselect ui-widget ui-state-default ui-corner-all").addClass(b.classes).attr({title:a.attr("title"),"aria-haspopup":!0,tabIndex:a.attr("tabIndex")}).insertAfter(a);(this.buttonlabel=d("<span />")).html(b.noneSelectedText).appendTo(a);var a=(this.menu=d("<div />")).addClass("ui-multiselect-menu ui-widget ui-widget-content ui-corner-all").addClass(b.classes).appendTo(document.body),c=(this.header=d("<div />")).addClass("ui-widget-header ui-corner-all ui-multiselect-header ui-helper-clearfix").appendTo(a);(this.headerLinkContainer=d("<ul />")).addClass("ui-helper-reset").html(function(){return!0===b.header?'<li><a class="ui-multiselect-all" href="#"><span class="ui-icon ui-icon-check"></span><span>'+b.checkAllText+'</span></a></li><li><a class="ui-multiselect-none" href="#"><span class="ui-icon ui-icon-closethick"></span><span>'+b.uncheckAllText+"</span></a></li>":"string"===typeof b.header?"<li>"+b.header+"</li>":""}).append('<li class="ui-multiselect-close"><a href="#" class="ui-multiselect-close"><span class="ui-icon ui-icon-circle-close"></span></a></li>').appendTo(c);(this.checkboxContainer=d("<ul />")).addClass("ui-multiselect-checkboxes ui-helper-reset").appendTo(a);this._bindEvents();this.refresh(!0);b.multiple||a.addClass("ui-multiselect-single")},_init:function(){!1===this.options.header&&this.header.hide();this.options.multiple||this.headerLinkContainer.find(".ui-multiselect-all, .ui-multiselect-none").hide();this.options.autoOpen&&this.open();this.element.is(":disabled")&&this.disable()},refresh:function(a){var b=this.element,c=this.options,f=this.menu,h=this.checkboxContainer,g=[],e="",i=b.attr("id")||k++;b.find("option").each(function(b){d(this);var a=this.parentNode,f=this.innerHTML,h=this.title,k=this.value,b="ui-multiselect-"+(this.id||i+"-option-"+b),l=this.disabled,n=this.selected,m=["ui-corner-all"],o=(l?"ui-multiselect-disabled ":" ")+this.className,j;"OPTGROUP"===a.tagName&&(j=a.getAttribute("label"),-1===d.inArray(j,g)&&(e+='<li class="ui-multiselect-optgroup-label '+a.className+'"><a href="#">'+j+"</a></li>",g.push(j)));l&&m.push("ui-state-disabled");n&&!c.multiple&&m.push("ui-state-active");e+='<li class="'+o+'">';e+='<label for="'+b+'" title="'+h+'" class="'+m.join(" ")+'">';e+='<input id="'+b+'" name="multiselect_'+i+'" type="'+(c.multiple?"checkbox":"radio")+'" value="'+k+'" title="'+f+'"';n&&(e+=' checked="checked"',e+=' aria-selected="true"');l&&(e+=' disabled="disabled"',e+=' aria-disabled="true"');e+=" /><span>"+f+"</span></label></li>"});h.html(e);this.labels=f.find("label");this.inputs=this.labels.children("input");this._setButtonWidth();this._setMenuWidth();this.button[0].defaultValue=this.update();a||this._trigger("refresh")},update:function(){var a=this.options,b=this.inputs,c=b.filter(":checked"),f=c.length,a=0===f?a.noneSelectedText:d.isFunction(a.selectedText)?a.selectedText.call(this,f,b.length,c.get()):/\d/.test(a.selectedList)&&0<a.selectedList&&f<=a.selectedList?c.map(function(){return d(this).next().html()}).get().join(", "):a.selectedText.replace("#",f).replace("#",b.length);this.buttonlabel.html(a);return a},_bindEvents:function(){function a(){b[b._isOpen? "close":"open"]();return!1}var b=this,c=this.button;c.find("span").bind("click.multiselect",a);c.bind({click:a,keypress:function(a){switch(a.which){case 27:case 38:case 37:b.close();break;case 39:case 40:b.open()}},mouseenter:function(){c.hasClass("ui-state-disabled")||d(this).addClass("ui-state-hover")},mouseleave:function(){d(this).removeClass("ui-state-hover")},focus:function(){c.hasClass("ui-state-disabled")||d(this).addClass("ui-state-focus")},blur:function(){d(this).removeClass("ui-state-focus")}});this.header.delegate("a","click.multiselect",function(a){if(d(this).hasClass("ui-multiselect-close"))b.close();else b[d(this).hasClass("ui-multiselect-all")?"checkAll":"uncheckAll"]();a.preventDefault()});this.menu.delegate("li.ui-multiselect-optgroup-label a","click.multiselect",function(a){a.preventDefault();var c=d(this),g=c.parent().nextUntil("li.ui-multiselect-optgroup-label").find("input:visible:not(:disabled)"),e=g.get(),c=c.parent().text();!1!==b._trigger("beforeoptgrouptoggle",a,{inputs:e,label:c})&&(b._toggleChecked(g.filter(":checked").length!==g.length,g),b._trigger("optgrouptoggle",a,{inputs:e,label:c,checked:e[0].checked}))}).delegate("label","mouseenter.multiselect",function(){d(this).hasClass("ui-state-disabled")||(b.labels.removeClass("ui-state-hover"),d(this).addClass("ui-state-hover").find("input").focus())}).delegate("label","keydown.multiselect",function(a){a.preventDefault();switch(a.which){case 9:case 27:b.close();break;case 38:case 40:case 37:case 39:b._traverse(a.which,this);break;case 13:d(this).find("input")[0].click()}}).delegate('input[type="checkbox"], input[type="radio"]',"click.multiselect",function(a){var c=d(this),g=this.value,e=this.checked,i=b.element.find("option");this.disabled||!1===b._trigger("click",a,{value:g,text:this.title,checked:e})?a.preventDefault():(c.focus(),c.attr("aria-selected",e),i.each(function(){this.value===g?this.selected=e:b.options.multiple||(this.selected=!1)}),b.options.multiple||(b.labels.removeClass("ui-state-active"),c.closest("label").toggleClass("ui-state-active",e),b.close()),b.element.trigger("change"),setTimeout(d.proxy(b.update,b),10))});d(document).bind("mousedown.multiselect",function(a){b._isOpen&&(!d.contains(b.menu[0],a.target)&&!d.contains(b.button[0],a.target)&&a.target!==b.button[0])&&b.close()});d(this.element[0].form).bind("reset.multiselect",function(){setTimeout(d.proxy(b.refresh,b),10)})},_setButtonWidth:function(){var a=this.element.outerWidth(),b=this.options;/\d/.test(b.minWidth)&&a<b.minWidth&&(a=b.minWidth);this.button.width(a)},_setMenuWidth:function(){var a=this.menu,b=this.button.outerWidth()-parseInt(a.css("padding-left"),10)-parseInt(a.css("padding-right"),10)-parseInt(a.css("border-right-width"),10)-parseInt(a.css("border-left-width"),10);a.width(b||this.button.outerWidth())},_traverse:function(a,b){var c=d(b),f=38===a||37===a,c=c.parent()[f?"prevAll":"nextAll"]("li:not(.ui-multiselect-disabled, .ui-multiselect-optgroup-label)")[f?"last":"first"]();c.length?c.find("label").trigger("mouseover"):(c=this.menu.find("ul").last(),this.menu.find("label")[f? "last":"first"]().trigger("mouseover"),c.scrollTop(f?c.height():0))},_toggleState:function(a,b){return function(){this.disabled||(this[a]=b);b?this.setAttribute("aria-selected",!0):this.removeAttribute("aria-selected")}},_toggleChecked:function(a,b){var c=b&&b.length?b:this.inputs,f=this;c.each(this._toggleState("checked",a));c.eq(0).focus();this.update();var h=c.map(function(){return this.value}).get();this.element.find("option").each(function(){!this.disabled&&-1<d.inArray(this.value,h)&&f._toggleState("selected",a).call(this)});c.length&&this.element.trigger("change")},_toggleDisabled:function(a){this.button.attr({disabled:a,"aria-disabled":a})[a?"addClass":"removeClass"]("ui-state-disabled");var b=this.menu.find("input"),b=a?b.filter(":enabled").data("ech-multiselect-disabled",!0):b.filter(function(){return!0===d.data(this,"ech-multiselect-disabled")}).removeData("ech-multiselect-disabled");b.attr({disabled:a,"arial-disabled":a}).parent()[a?"addClass":"removeClass"]("ui-state-disabled");this.element.attr({disabled:a,"aria-disabled":a})},open:function(){var a=this.button,b=this.menu,c=this.speed,f=this.options,h=[];if(!(!1===this._trigger("beforeopen")||a.hasClass("ui-state-disabled")||this._isOpen)){var g=b.find("ul").last(),e=f.show,i=a.offset();d.isArray(f.show)&&(e=f.show[0],c=f.show[1]||this.speed);e&&(h=[e,c]);g.scrollTop(0).height(f.height);d.ui.position&&!d.isEmptyObject(f.position)?(f.position.of=f.position.of||a,b.show().position(f.position).hide()):b.css({top:i.top+a.outerHeight(),left:i.left});d.fn.show.apply(b,h);this.labels.eq(0).trigger("mouseover").trigger("mouseenter").find("input").trigger("focus");a.addClass("ui-state-active");this._isOpen=!0;this._trigger("open")}},close:function(){if(!1!==this._trigger("beforeclose")){var a=this.options,b=a.hide,c=this.speed,f=[];d.isArray(a.hide)&&(b=a.hide[0],c=a.hide[1]||this.speed);b&&(f=[b,c]);d.fn.hide.apply(this.menu,f);this.button.removeClass("ui-state-active").trigger("blur").trigger("mouseleave");this._isOpen=!1;this._trigger("close")}},enable:function(){this._toggleDisabled(!1)},disable:function(){this._toggleDisabled(!0)},checkAll:function(){this._toggleChecked(!0);this._trigger("checkAll")},uncheckAll:function(){this._toggleChecked(!1);this._trigger("uncheckAll")},getChecked:function(){return this.menu.find("input").filter(":checked")},destroy:function(){d.Widget.prototype.destroy.call(this);this.button.remove();this.menu.remove();this.element.show();return this},isOpen:function(){return this._isOpen},widget:function(){return this.menu},getButton:function(){return this.button},_setOption:function(a,b){var c=this.menu;switch(a){case "header":c.find("div.ui-multiselect-header")[b?"show":"hide"]();break;case "checkAllText":c.find("a.ui-multiselect-all span").eq(-1).text(b);break;case "uncheckAllText":c.find("a.ui-multiselect-none span").eq(-1).text(b);break;case "height":c.find("ul").last().height(parseInt(b,10));break;case "minWidth":this.options[a]=parseInt(b,10);this._setButtonWidth();this._setMenuWidth();break;case "selectedText":case "selectedList":case "noneSelectedText":this.options[a]=b;this.update();break;case "classes":c.add(this.button).removeClass(this.options.classes).addClass(b);break;case "multiple":c.toggleClass("ui-multiselect-single",!b),this.options.multiple=b,this.element[0].multiple=b,this.refresh()}d.Widget.prototype._setOption.apply(this,arguments)}})})(jQuery);


function IsEmail(email) {
  var regex = /^([a-zA-Z0-9_.+-])+\@(([a-zA-Z0-9-])+\.)+([a-zA-Z0-9]{2,4})+$/;
  return regex.test(email);
}


jQuery.fn.highlight = function (search_query) {
    var regex = new RegExp(search_query, "gi");
    return this.each(function () {
        this.innerHTML = this.innerHTML.replace(regex, function(matched) {
            return "<span class='wf_light'>" + matched + "</span>";
        });
    });
};

function txt_len_counter(cur_el, el){
    var maxLen = $(cur_el).attr('maxlength')
    var curLen = $(cur_el).val().length
    if(curLen >= maxLen){
        $(cur_el).val($(cur_el).val().substr(0, maxLen))
    }
    var remaning = maxLen - curLen
    if(remaning < 0){
        remaning = 0
    }
    $(el).html('(осталось символов: ' + remaning + ')')
}

function get_today(){
    var today = new Date();
    var dd = today.getDate();
    var mm = today.getMonth()+1;
    if(dd<10){dd='0'+dd} 
    if(mm<10){mm='0'+mm} 
    today = today.getFullYear() + '-' + mm + '-' + dd;
    return today
}



$(document).ready(function(){
    setInterval(function(){$('.new_msg_indicator').effect('pulsate', {color: 'white'}, 1500)}, 5000);

    $('.full_website').click(function(e){
        e.preventDefault()
        var domain = $(this).attr('href').replace('http://www.','').replace('http://m.','').replace('http://','')
        var id = $(this).attr('id').replace('fw_type_','')
        $.cookie("mobile", id, { expires: 7, path: "/", domain: domain})
        window.location.replace($(this).attr('href'))
    });

    $('.top-menu-icon').click(function(){
        $('.art-posttree-width').toggle("slide", {direction:"left"});
    });

    $('.youtube_wrapper').click(function(){
        $img = $(this).find('img')
        var id = $img.attr('id').replace('yt_','')
        var html = '<iframe width="250" height="150" src="//www.youtube.com/embed/' + id + '?rel=0&autoplay=1" frameborder="0" allowfullscreen></iframe>'
        $(this).html(html)
    });


    /*call menu panel*/
    $(".art-menu__title-menu").click(function()
    {
        $(".art-menu").toggle("slide", {direction:"right"});
        $(".art-search").hide();
    });

    /*call search panel*/
    $(".art-search__title-search").click(function()
    {
        $(".art-search").toggle("slide", {direction:"left"});
        $(".art-menu").hide();
        $(".search-field").focus();
    });

    /*icon for close page*/
    $(".page-close").click(function(){
        $(".page").css({"display": "none"});
        $(".page-close").css({"display": "none"});
        $(".gridster").css({'display':'block'})
    });

    /*accordion for api list methods*/
    $('.method-category').click(function(){
        $.cookie("openItem", this.getAttribute("id"), {
            expires: 7,
            path: "/",
        });
    });
    if($.cookie("openItem")){
        openitem = $('#' + $.cookie("openItem"))
    }else{
        openitem = false
    }

    $('#accordion').accordion({ active: openitem })
    $('#accordion').accordion({ clearStyle: true })



    $("select[name='films']").change(function(){
        var el = $(this).val()
        $("#total div").css('display', 'none')
        $("#film"+el).css('display', 'inline-block')
    });
    $("select[name='films_v3']").change(function(){
        var el = $(this).val()
        $("#total_v3 div").css('display', 'none')
        $("#film_v3_"+el).css('display', 'inline-block')
    });


    $(".api-description").mouseover(function(){
        $(".api-description__edit-button").css({"display": "inline-block"})
    });
    $(".api-description").mouseout(function(){
        $(".api-description__edit-button").css({"display": "none"})
    });

});
/*
$(document).delegate('.ui-multiselect-checkboxes li', 'click', function(){
    var check = $(this).find('input[type="checkbox"]').prop('checked')
    alert(check)
});*/

$(document).delegate('.kinoafisha_button', 'click', function(){
    $.fancybox.open($('.kinoafisha_login').show())
});
    
$(document).delegate('.kinoafisha_auth', 'click', function(){
    var nick = $('.nickname').val()
    if(nick.replace(/\s+/g, '')){
        $('.nickname').css({'border': '1px solid #BCBCBC'})
        $('.nickname_2').html(nick)
        $('.nickname').hide()
        $('.kinoafisha_btn').prop('disabled', true)
        Dajaxice.user_registration.get_kinoafisha_user(get_kinoafisha_user_callback, {'nick': nick})
    }else{
        $('.nickname').css({'border': '1px solid red'})
    }
});

$(document).delegate('.ka_auth_no', 'click', function(){
    $('.nickname_2, .kinoafisha_q').html('')
    $('.nickname').val('').show()
    $('.ka_btns').html('<input type="button" value="Вперед!" class="kinoafisha_auth kinoafisha_btn" />')
});

$(document).delegate('.ka_auth_yes', 'click', function(){
    var nick = $('.nickname').val()
    if(nick.replace(/\s+/g, '')){
        $('.kinoafisha_btn').prop('disabled', true)
        Dajaxice.user_registration.get_kinoafisha_user_list(get_kinoafisha_user_callback, {'nick': nick})
    }
});

$(document).delegate('.ka_auth_next', 'click', function(){
    $('.kinoafisha_btn').prop('disabled', true)
    var val = $('.ka_user_list').children(":selected").val()
    Dajaxice.user_registration.get_kinoafisha_user(get_kinoafisha_user_callback, {'nick': '', 'id': val})
});

$(document).delegate('.kinoafisha_auth_fin', 'click', function(){
    $('.kinoafisha_btn').prop('disabled', true)
    var id = $('.kinoafisha_uid').val()
    var q1 = $('.kq_num1').val()
    var q2 = $('.kq_num2').val()
    var q3 = $('.kq_num3').val()
    
    q1 = typeof q1 !== 'undefined' ? q1 : ''
    q2 = typeof q2 !== 'undefined' ? q2 : ''
    q3 = typeof q3 !== 'undefined' ? q3 : ''
    
    $('.ka_err').hide()
    
    Dajaxice.user_registration.kinoafisha_auth(kinoafisha_auth_callback, {'id': id, 'q1': q1, 'q2': q2, 'q3': q3})
});

function kinoafisha_auth_callback(data){
    $('.kinoafisha_btn').prop('disabled', false)
    if(data.status){
        if(data.error.length){
            $('.ka_err').html(data.error).show()
        }else{
            $.fancybox.close()
            window.location.replace(data.redirect_to)
        }
    }else{
        $.fancybox.close()
        location.reload()
    }
}


function get_kinoafisha_user_callback(data){
    $('.kinoafisha_btn').prop('disabled', false)
    if(data.status){
        if(data.content.length){
            $('.kinoafisha_q').html(data.content)
            $('.ka_btns').html(data.btns)
            $('.nickname_2').html(data.nickname)
            $.fancybox.update()
        }else{
            $('.nickname_2, .kinoafisha_q').html('')
            $('.nickname').val('').show()
            $('.ka_btns').html(data.btns)
        }
    }
}

/*gridster blocks menu
$(function(){
    $(".gridster ul").gridster({
        widget_margins: [11, 25],
        widget_base_dimensions: [100, 100],
        min_rows: 3,
    });
});
*/
/*call api page*/
function my_js_callback(data){
    $(".page").css({'display':'block'})
    $(".page-close").css({'display':'block'})
    $(".gridster").css({'display':'none'})
    $(".page").html(data)
    $("#accordion").accordion()
    $('#accordion').accordion({ clearStyle: true })
}

/*reload main page*/
function dumps_options(){
    $(".art-postcontent").load();
}

function get_details(method){
    Dajaxice.base.get_details(details, {'method': method})
}

function content_height(cl, val){
    var scroll_h = ($(window).height() / 100) * val
    $(val).css('height', scroll_h + 'px')
}

/* begin UserRegistration */
function warning(data){
    if(data != ''){
        alert(data)
    }
}

function settings(check, id){
    Dajaxice.user_registration.sett(warning, {'value':check, 'id':id})
}

function get_countries_cities_callback(data){
    var html = '<b>Укажите Ваш город</b>:<br /><br />' + data.countries + data.cities
    html += '<input type="button" value="Выбрать" class="set_my_city" />'
    $.fancybox(html)
}

function set_my_city_callback(data){
    if(data.status){
        location.reload()
    }
}

function booking_article_edit(){
    id = $('.booking-article-id').val()
    title = $('.txt_wrapper h3').text()
    text = $('.txt_wrapper .btxt').text()
    $('.booking-add-article').click()
    $('input[name="edit"]').val(id)
    $('input[name="news_title"]').val(title)
    tinyMCE.getInstanceById('id_text').setContent(text)
    $.fancybox.close()
}
function booking_article_remove_callback(data){
    if(data.status){
        $('#booking-article-item-' + data.content).remove()
        $.fancybox.close()
    }
}
function booking_article_remove(id){
    if (confirm("Вы уверены, что хотите удалить?")) {
        Dajaxice.base.booking_article_remove(booking_article_remove_callback, {'id': id})
    }
}
function get_booking_article_callback(data){
    if(data.status){
        $.fancybox(data.content)
    }
}
function get_booking_article(id){
    Dajaxice.base.get_booking_article(get_booking_article_callback, {'id': id})
}

function booking_get_hall_data_callback(data){
    if(data.status){
        $('#' + data.parent_id + ' .booking-sch-items').html(data.content)
        $('#' + data.parent_id + ' .booking-date-range').html('')
        for(i in data.date_range){
            $('#' + data.parent_id + ' .booking-date-range').append('<option value="' + data.date_range[i].from + '">' + data.date_range[i].from_str + '-' + data.date_range[i].to_str + '</option>')
        }
    }
    $('.booking-halls').prop('disabled', false)
}


$(document).delegate('.booking-add-container-close', 'click', function(){
    $.fancybox.close()
    $('.booking-add-container').find('.booking-add-dates:not(:first)').remove()
    $('.booking-add-sch-bl, .booking-add-save-msg').html('')
    $('input[name="date_from"], input[name="date_to"]').attr('id', null).attr('class', null).val('')
    $(".booking-add-halls").multiselect("uncheckAll")
    $('.booking-edit-sch-id').val('')
    $('.booking-add-real-bl, .booking-del-sch').remove()
});


$(document).delegate('.booking-del-sch', 'click', function(){
    if(confirm('Вы уверены, что хотите удалить сеансы?')) {
        var id = $(this).attr('id').replace('del_','')
        $('.booking-add-save').prop('disabled', true)
        Dajaxice.base.get_booking_del_sch(booking_add_sch_callback, {'id': id})
    }
});

function booking_add_sch_callback(data){
    $('.booking-add-save-msg').html('')
    if(data.status){
        $('.booking-add-save-msg').html('Загрузка...')
        location.reload()
    }else{
        $('.booking-add-save').prop('disabled', false)
    }
}

$(document).delegate('.booking-get-excel-btn', 'click', function(){
    var halls = []
    $('.booking-get-excel-halls option:selected').each(function(){
        halls.push($(this).val())
    })

    if(!halls.length){
        $('.booking-get-excel-halls').next().effect('highlight', {color: '#ff5c33'})
    }else{
        date_from = $('input[name="ex_date_from"]').val()
        date_to = $('input[name="ex_date_to"]').val()

        next = true
        if(!date_from){
            $('input[name="ex_date_from"]').effect('highlight', {color: '#ff5c33'})
            next = false
        }
        if(!date_to){
            $('input[name="ex_date_to"]').effect('highlight', {color: '#ff5c33'})
            next = false
        }
        if(next){
            $(this).parent().submit()
        }
    }
});

$(document).delegate('.booking-add-save', 'click', function(){
    var halls = []
    $('.booking-add-halls option:selected').each(function(){
        halls.push($(this).val())
    })

    if(!halls.length){
        $('.booking-add-halls').next().effect('highlight', {color: '#ff5c33'})
    }else{
        var data = []
        $('.booking-add-container').find('.booking-add-dates').each(function(index){

            date_from = $(this).find('input[name="date_from"]').val()
            date_to = $(this).find('input[name="date_to"]').val()

            films = []
            $(this).find('.booking-add-releases option:selected').each(function(){
                films.push($(this).val())
            })

            if(films.length || date_from || date_to){
                next = true
                if(!films.length){
                    $(this).find('.booking-add-releases').next().effect('highlight', {color: '#ff5c33'})
                    next = false
                }
                if(!date_from){
                    $(this).find('input[name="date_from"]').effect('highlight', {color: '#ff5c33'})
                    next = false
                }
                if(!date_to){
                    $(this).find('input[name="date_to"]').effect('highlight', {color: '#ff5c33'})
                    next = false
                }
                if(next){
                    index += 1
                    $(this).attr('id', 'boo_' + index)
                    data.push({
                        'index': index,
                        'from': date_from,
                        'to': date_to,
                        'films': films,
                    })
                }
            }
        });

        if(data.length){
            $('.booking-add-save').prop('disabled', true)
            $('.booking-add-save-msg').html('Сохранение...')
            var edit = $('.booking-edit-sch-id').val()
            var real = $('.booking-add-real').prop('checked')
            real = typeof real !== 'undefined' ? real : false;
            Dajaxice.base.booking_add_sch(booking_add_sch_callback, {'halls': halls, 'data': data, 'edit': edit, 'real': real})
        }
    }
});


/*
$(document).delegate('.booking-add-dates-range', 'click', function(){
    $obj = $('.booking-add-range-dates').first().clone()
    $obj.find('input[name="date_from"], input[name="date_to"]').attr('id', null).attr('class', null).val('')
    
    $(this).before($obj)
    $.fancybox.update()

    $('input[name="date_from"], input[name="date_to"]').datepicker({
        altFormat: "yy-mm-dd",
        dateFormat: 'yy-mm-dd',
        changeMonth: true,
        changeYear: true,
        firstDay: 1
    });

});*/

function booking_set_calendar(el1, el2, val){
    $(el1).datepicker({
        altFormat: "yy-mm-dd",
        dateFormat: 'yy-mm-dd',
        changeMonth: true,
        changeYear: true,
        firstDay: 1,
        onClose: function( selectedDate ) {
            $(this).parent().find(el2).datepicker( "option", val, selectedDate );
        }
    });
}


$(document).delegate('.booking-add-range', 'click', function(){
    $obj = $(this).parent().clone().attr('id', null)

    $('.booking-add-save').before($obj.effect('highlight'))
    
    $obj.find('input[name="date_from"], input[name="date_to"]').attr('id', null).attr('class', null).val('')
    
    $releases = $('#original').clone().attr('id', null)
    $obj.find('.booking-add-sch-bl').html('').append($releases.show())

    $releases.find('.booking-add-releases').multiselect({ 
        selectedList: 10,
        noneSelectedText: 'Релиз не выбран',
        minWidth: 425,
    })

    booking_set_calendar('input[name="date_from"]', 'input[name="date_to"]', 'minDate')
    booking_set_calendar('input[name="date_to"]', 'input[name="date_from"]', 'maxDate')

    $.fancybox.update()
});


$(document).delegate('.booking-copy-range', 'click', function(){
    $obj = $(this).parent().clone().attr('id', null)
    
    var checked = []
    $(this).parent().find('.booking-add-releases option:selected').each(function(){
        checked.push($(this).val())
    })

    $obj.find('input[name="date_from"], input[name="date_to"]').attr('id', null).attr('class', null)
    
    $releases = $('#original').clone().attr('id', null)
    $obj.find('.booking-add-sch-bl').html('').append($releases.show())

    $releases.find('option').each(function(){
        if($.inArray($(this).val(), checked) > -1){
            $(this).prop('selected', true)
        }
    })

    $releases.find('.booking-add-releases').multiselect({ 
        selectedList: 10,
        noneSelectedText: 'Релиз не выбран',
        minWidth: 425,
        header: false,
    })
    
    $('.booking-add-save').before($obj.effect('highlight'))

    booking_set_calendar('input[name="date_from"]', 'input[name="date_to"]', 'minDate')
    booking_set_calendar('input[name="date_to"]', 'input[name="date_from"]', 'maxDate')

    $.fancybox.update()
});

function booking_edit_sch_callback(data){
    if(data.status){
        
        $('.booking-add-halls option[value="' + data.content.hall_id + '"]').prop('selected', true)

        $('.booking-add-schedules-btn').first().click()
        $('.booking-add-dates .booking-add-range, .booking-add-dates .booking-copy-range').hide()
        $('input[name="date_from"]').val(data.content.from)
        $('input[name="date_to"]').val(data.content.to)
        for(i in data.content.films){
            $('.booking-add-sch-bl .booking-add-releases option[value="' + data.content.films[i] + '"]').prop('selected', true)
        }
        $('.booking-add-sch-bl .booking-add-releases').multiselect("refresh")
        $('.booking-add-halls').multiselect("refresh")
        $('.booking-edit-sch-id').val(data.content.id)

        var html = '<div class="booking-add-real-bl"><div>Утвердить</div><div> <input type="checkbox" class="booking-add-real" /></div></div>'
        $('.booking-add-releases-container').append(html)
        $('.booking-add-dates .booking-add-range').after('<span class="delete_btn booking-del-sch" id="del_' + data.id + '" title="Удалить"></span>')
    }
}

$(document).delegate('.booking-sch-item-edit', 'click', function(){
    var id = $(this).attr('id')
    Dajaxice.base.booking_edit_sch(booking_edit_sch_callback, {'id': id})
});

$(document).delegate('.booking-add-schedules-btn', 'click', function(){
    $(".booking-add-halls").multiselect({ 
        selectedList: 10,
        noneSelectedText: 'Зал не выбран',
        minWidth: 325,
    })
    $releases = $('#original').clone().attr('id', null)
    $('.booking-add-sch-bl').append($releases.show())
    $releases.find(".booking-add-releases").multiselect({ 
        selectedList: 10,
        noneSelectedText: 'Релиз не выбран',
        minWidth: 425,
        header: false,
    })
    booking_set_calendar('input[name="date_from"]', 'input[name="date_to"]', 'minDate')
    booking_set_calendar('input[name="date_to"]', 'input[name="date_from"]', 'maxDate')
    $('.booking-edit-sch-id').val('')
    $('.booking-add-dates .booking-add-range, .booking-add-dates .booking-copy-range').show()
    $.fancybox($('.booking-add-container'), {'modal': true})
});


$(document).ready(function(){

    $('.booking-halls').change(function(){
        parent_id = $(this).parents('.booking-sch-col').attr('id')
        id = $(this).val()
        $(this).prop('disabled', true)
        Dajaxice.base.booking_get_hall_data(booking_get_hall_data_callback, {'id': id, 'parent': parent_id})
    });

    $('.booking-date-range').change(function(){
        parent_id = $(this).parents('.booking-sch-col').attr('id')
        val = $(this).val()
        $('#' + parent_id + ' .bsi').hide()
        $('#' + parent_id + ' #from_' + val).show()
    });


    $('.booker-cinema').click(function(){
        $parent = $(this).parent()

        if($parent.attr('class') == 'booker-exist-cinemas-bl'){

            parent_exist = $('.booker-selected-cinemas #' + $parent.attr('id')).length
            if(!parent_exist){
                $('.booker-selected-cinemas').append('<div class="booker-selected-cinemas-bl" id="' + $parent.attr('id') + '"></div>')
            }

            $city = $('.booker-exist-cities option:selected')

            $selected_exist = $('.booker-selected-cities option[value="' + $city.val() + '"]')
            if($selected_exist.length){
                $selected_exist.prop('selected', true)
            }else{
                $('<option value="' + $city.val() + '" selected>' + $city.text() + '</option>').appendTo('.booker-selected-cities')
            }
            
            $(this).appendTo('.booker-selected-cinemas #' + $parent.attr('id'))
            cinemas = $('input[name="cinemas"]').val()
            cinemas += $(this).attr('id') + ';'
            $('input[name="cinemas"]').val(cinemas)
            $('.booker-selected-cinemas-bl').hide()
            $('.booker-selected-cinemas #' + $parent.attr('id')).show()
            
        }else{

            $city = $('.booker-selected-cities option:selected')

            $('.booker-exist-cities option[value="' + $city.val() + '"]').prop('selected', true)
            
            $(this).appendTo('.booker-exist-cinemas #' + $parent.attr('id'))

            cinemas = ''
            $('.booker-selected-cinemas').find('.booker-cinema').each(function(){
                cinemas += $(this).attr('id') + ';'
            })
            $('input[name="cinemas"]').val(cinemas)
            $('.booker-exist-cinemas-bl').hide()
            $('.booker-exist-cinemas #' + $parent.attr('id')).show()
        }
    });

    $('.select_mycity').click(function(){
        Dajaxice.user_registration.get_countries_cities(get_countries_cities_callback, {})
    });

    function slide_down(s, h){
        $(h).hide();
        $(s).show();
    }
    $('.email_button p').click(function(){
	    slide_down('.email_button .hidden_input', '.email_button p')
    });

    $('.lj_button p').click(function(){
	    slide_down('.lj_button .hidden_input', '.lj_button p')
    });

    function get_data_callback(data){
        if(data.status == true){
            if(window.location.host == 'letsgetrhythm.com.au' || window.location.host == 'vladaalfimovdesign.com.au'){all = 'FOR ALL'}else{all = 'ДЛЯ ВСЕХ'}
            $('.city_in_card').html('');
            if(data.all == true){
                $('<option value="">' + all + '</option>').appendTo('.city_in_card');
            }
            for(i in data.content) {
                var option = $('<option value="' + data.content[i].key + '">' + data.content[i].name + '</option>').appendTo('.city_in_card');
            }
            $('.city_in_card').prop('disabled', false);
        }
    }

    $(document).delegate('.country_in_card', 'change', function(){
	    $('.city_in_card').prop('disabled', true);
	    title = $('.city_in_card').attr('title');
	    id = $('.country_in_card').val();
	    if(id){
	        Dajaxice.user_registration.get_cities(get_data_callback, {'id': id, 'title': title})
	    }
    });

    $(document).delegate('.set_my_city', 'click', function(){
        var country = $(".country_in_card option:selected").val();
        var city = $(".city_in_card option:selected").val();
        $(this).prop('disabled', true)
        $(this).after('<br />Сохраняем...')
        Dajaxice.person.country_city(set_my_city_callback, {'id': '0', 'country': country, 'city': city});
    });
    


    $(".acc_del").click(function(){
        if(window.location.host == 'letsgetrhythm.com.au' || window.location.host == 'vladaalfimovdesign.com.au'){msg = 'Delete'}else{msg = 'Are you sure you want to delete this account?'}
        if (confirm(msg)) {
            $(this).parents('form').submit();
        }
    });

});

/* end UserRegistration */

/* begin Import Panel */
function get_data_callback(data){
    $('#data_select').prop('disabled', false);
    $('#show_relations').prop('disabled', false);
    $('#data_select').html('');
    if(data.status == 'True'){
        if(data.content){
            $('#rel').prop('disabled', false);
            $('#kid_sid').prop('disabled', false);
        }
        for(i in data.content) {
            var option = $('<option value="' + i + '">' + data.content[i] + '</option>').appendTo('#data_select');
        }
    }else{
        var option = $('<option value="">пусто</option>').appendTo('#data_select');
    }
}

function get_data(type){
    var value = $('#get_data_name').attr('value')
    var kid = $('#nof_data').find(":selected").attr('value');
    if(!kid){
        kid = $('input:radio[class="radio_checker"]:checked').val();
    }
    var all_data = $('#check_all_data').attr('checked')
    if($('#check_all_data').attr('checked')){
        var all_data = true
    }else{
        var all_data = false
    }
    if(value){
        $('#data_select').prop('disabled', true);
        $('#show_relations').prop('disabled', true);
        $('#rel').prop('disabled', true);
        $('#kid_sid').prop('disabled', true);
        Dajaxice.release_parser.get_data(get_data_callback, {'value': value, 'kid': kid, 'type': type, 'all_data': all_data})
    }
}

function get_data_checker(type){
    var value = $('#get_data_name').attr('value')
    var kid = '*'
    var all_data = false
    $('#data_select').prop('disabled', true);
    Dajaxice.release_parser.get_data(get_data_callback, {'value': value, 'kid': kid, 'type': type, 'all_data': all_data})
}

/* end Import Panel */

/* begin News */
function subscriber(type, id){
    var email_exist = $('#subscribe_form-email').attr('email-exist')
    var next = true
    var email = ''
    if(email_exist == '0'){
        email = $('#subscribe_form-email').val()
        if(!IsEmail(email)){
            $('#subscribe_form-bl').show()
            $('#subscribe_form-msg').html('Введите E-Mail правильно!<br /><br />')
            next = false
        }
    }
    if(next){
        $('#subscribe_form-msg').html('')
        $('#subscribe_form-bl').hide()
        Dajaxice.user_registration.subscriber(subscribe_me_callback, {'email': email, 'type': type, 'id': id})
    }
}

function subscribe_me_callback(data){
    
    if(data.error){
        $('#subscribe_form-msg').html(data.content + '<br /><br />')
        if(data.email_error){
            $('#subscribe_form-email').val('').show()
            $('#subscribe_form-bl').show()
        }
    }else{
        $('#subscribe_form-msg').html(data.content + '<br />')
        $('#subscribe_form-email, #subscribe_form-btn').remove()
    }
}

$(document).ready(function(){
    $('.comments_subscribe').on('change', function(){
        $parent = $(this).parents('.comments_block')
        var email_exist = $parent.find('#comments_subscribe_form-email').attr('email-exist')
        if($(this).prop('checked')){
            if(email_exist == '0'){
                $parent.find('.comments_subscribe-bl').show()
            }
        }else{
            $parent.find('.comments_subscribe-bl').hide()
        }
    });

    $(".news_txt").click(function(){
        $(".news_txt").hide();
        $(".news_text").hide();
        $('.organization_txt').show();
    });
    $(".organization_txt_cancel_btn").click(function(){
        $('.organization_txt').hide();
        $(".news_txt").show();
        $(".news_text").show();
    });


    $(".news_new").click(function(){
        $.fancybox.open($(".new_new").show());
    });

    $(".news_del").click(function(){
        if (confirm("Вы уверены, что хотите удалить?")) {
            $('.new_del').submit();
        }
    });

    $("#news_poster").hover(
        function(){
            $('.news_poster_edit').show();
        },
        function(){
            $('.news_poster_edit').hide();
        }
    );

    $(".news_poster_edit").click(function(){
        $(".news__img").hide();
        $('.trailer').hide();
        $("#news_poster").append($('.news_form_poster').show());
    });
    $(".news_poster_cancel_btn").click(function(){
        $(".news__img").show();
        $('.trailer').show();
        $('.news_form_poster').hide();
    });

    $(".news_visible_btn").click(function(){
        news_visibles('visible');
    });

    $(".news_world_pub_btn").click(function(){
        news_visibles('world_pub');
    });
});

$(document).delegate('.news_title_accept_btn', 'click', function(){
    var id = $('.news_id').val();
    var val = $(".news_title_field").attr('value');
    if(val){
        Dajaxice.news.get_news_title(function(){}, {'id': id, 'val': val});
        $('.news_title_fields').hide();
        $('.news_title').html(val).show();
    }else{
        $('.title_err').html('!');
    }
});

$(document).delegate('.news_tags_accept_btn', 'click', function(){
    var id = $('.news_id').val();
    var arr = []
    $('.news_tags_field').each(function(){
        val = $(this).attr('value');
        if(val){
            arr.push(val);
        }
    });
    if(!arr.length){
        $('.news_tags_err').html('Укажите хотя бы одну метку');
    }else{
        Dajaxice.news.get_news_tags(get_news_tags_callback, {'id': id, 'arr': arr});
    }
});

function get_news_tags_callback(data){
    if(data.status == true){
        var tags = ''
        for(i in data.content){
            tags += data.content[i] + '; ';
        }
        $('.news_tags_fields').hide();
        $('.news_tags').html(tags).show();
    }
}

function news_form_poster_type(el){
    var type = $(el).val();
    $('.news_form_poster__img').hide();
    $('.news_form_poster__video').hide();
    $('.news_form_poster__' + type).show();
}

function news_visibles(type){
    var id = $('.news_id').val();
    var val = false
    if($(".news_" + type + "_check").is(':checked')){
        var val = true
    }
    Dajaxice.news.get_news_visibles(function(){}, {'id': id, 'val': val, 'type': type});
    $('.news_' + type + '_msg').html('OK').show().fadeOut(1500);

}

/* end News */

/* begin Film */
function lbe_new_clear(){
    var date = get_today()
    $('.lbe_list, .lbe_adv_info, .lbe_adv_balance_bl').hide()
    $('.lbe_new, .lbe_adv_new').show()
    $('.lbe_new_id, .lbe_new_adv_id, .background_new_id').val(0)
    $('.lbe_new_name').val('Баннер')
    $('.background_new_name').val('Фон')
    $('.lbe_new_datefrom').val(date)
    $('.lbe_new_dateto, .lbe_new_file, .lbe_new_url, .lbe_adv_new_anchor, .lbe_adv_new_url, .lbe_adv_new_text, .lbe_adv_new_budget, .background_new_file, .background_new_url').val('')
    $('.lbe_new_error, .lbe_adv_pre_text, .lbe_adv_pre_anchor, .lbe_adv_new_clicks, .lbe_adv_new_balance, .lbe_adv_new_balance_clicks').html('')
    $('.lbe_adv_pre_anchor').attr('href', '#')
    $('.lbe_new_name, .lbe_new_file, .lbe_new_datefrom, .lbe_new_dateto, .lbe_new_sites, .background_new_name, .background_new_file').css({'border': '1px solid #BCBCBC'})
    $('.lbe_new_sites').each(function(){
        if($(this).val() == '5'){
            $(this).prop('checked', true)
        }else{
            $(this).prop('checked', false)
        }
    });
}

function adv_item_remove(el, btype, id){
    if(confirm("Вы уверены, что хотите удалить?")){
        Dajaxice.base.del_lbe_item(function(){}, {'id': id, 'btype': btype})
        $(el).parents('tr').remove()
    }
}

function adv_item_clicks(id){
    Dajaxice.base.get_adv_item_clicks(get_adv_item_clicks_callback, {'id': id})
}

function get_adv_item_clicks_callback(data){
    $.fancybox(data.content)
}

$(document).delegate('.lbe_adv_anchor', 'mouseover', function(){
    $(this).parents('tr').find('.lbe_img').show()
});
$(document).delegate('.lbe_adv_anchor', 'mouseout', function(){
    $(this).parents('tr').find('.lbe_img').hide()
});
$(document).delegate('.lbe_item_del', 'click', function(){
    var $parent = $(this).parents('tr')
    var id = $parent.attr('id').replace('lbe_id_','')
    var t = $('.lbe_new_t').val()
    if(confirm("Вы уверены, что хотите удалить?")){
        Dajaxice.base.del_lbe_item(function(){}, {'id': id, 'btype': t})
        $parent.remove()
        $('#my_adv_' + id).remove()
    }
});
$(document).delegate('.lbe_adv_item_clicks a', 'click', function(){
    var id = $(this).attr('id').replace('my_adv_info_','')
    var visible = $('.lbe_list_tbl #my_adv_' + id).is(":visible")
    $parent = $(this).parents('table')
    $('tr[id^=my_adv_]').hide()
    if(!visible){
        $('.lbe_list_tbl #my_adv_' + id).show()
    }
});

$(document).delegate('.lbe_item_edit', 'click', function(){
    var $parent = $(this).parents('tr')
    var id = $parent.attr('id').replace('lbe_id_','')
    var name = $parent.find('.lbe_title').text()
    var url = $parent.find('.lbe_url').text()
    var date = $parent.find('.lbe_date_bl')
    var date_from = date.attr('fr')
    var date_to = date.attr('to')
    var country = $parent.find('.lbe_country').attr('id')
    var city = $parent.find('.lbe_city').attr('id')
    var places = $(this).attr('id').split(',')
    
    if(places.length){
        $('.lbe_new_sites').each(function(){
            check = false
            for(i in places){
                if($(this).val() == places[i]){
                    check = true
                }
            }
            $(this).prop('checked', check)
        });
    }

    $('.lbe_new_id, .lbe_new_adv_id').val(id)
    $('.lbe_new_name').val(name)
    $('.lbe_new_url').val(url)
    $('.lbe_new_datefrom').val(date_from)
    $('.lbe_new_dateto').val(date_to)
    
    $('.lbe_new').show()
    $('.lbe_list').hide()
    
    Dajaxice.user_registration.get_countries_cities_alt(lbe_countries_cities_callback, {'check_all': true, 'country': country, 'city': city})
    
});

function adv_item_edit(n, btype, id){
    id = typeof id !== 'undefined' ? id : 0;
    Dajaxice.base.get_adv_item_edit(get_adv_item_edit_callback, {'new': n, 'btype': btype, 'id': id})
}


function get_adv_item_edit_callback(data){
    if(data.status){
        $.fancybox(data.content)
        $('.left_banner_editor_bl-adv').show()
        if(data.t != 7){
            $('.lbe_adv_new').show()
        }
        Dajaxice.base.get_cities_adv(get_cities_adv_callback, {'country': data.country, 'city': data.city})
        $.getScript("/static/base/js/jquery.form.js")
        $.getScript("/static/base/js/jquery.mask.js", function() {
            $('.lbe_adv_new_budget').unmask().mask('00000')
        });

        var today = get_today()

        $('.background_new_start').datepicker({
            altFormat: "yy-mm-dd",
            dateFormat: 'yy-mm-dd',
            minDate: today,
            maxDate: "+2M",
            changeMonth: true,
            changeYear: true,
            firstDay: 1
        });


    }
}

$(document).delegate('.lbe_adv_item_edit', 'click', function(){
    $('.lbe_edit_cancel').show()
    $('.lbe_new_cancel').hide()

    var $parent = $(this).parents('tr')
    var id = $parent.attr('id').replace('lbe_id_','')
    var name = $parent.find('.lbe_adv_anchor').text()
    var url = $parent.find('.lbe_adv_url').text()
    var text = $parent.find('.lbe_adv_text').val()
    var budget = $parent.find('.lbe_adv_budget').val()
    var style = $parent.find('.lbe_adv_style').val()
    var country = $parent.find('.lbe_adv_country').attr('id')
    var city = $parent.find('.lbe_adv_city').attr('id').split(',')
    var balance = $parent.find('.lbe_adv_balance').val()
    var price = $('.lbe_new_adv_price').val()
    var clicks = parseInt(budget / price)
    $('.lbe_adv_new_clicks').html('= кликов: ' + clicks)

    var balance_clicks = parseInt(balance / price)
    $('.lbe_adv_new_balance').html(balance)
    $('.lbe_adv_new_balance_clicks').html('= кликов: ' + balance_clicks)
    $('.lbe_adv_balance_bl').show()

    $('.lbe_new_adv_id').val(id)
    $('.lbe_adv_new_anchor').val(name)
    $('.lbe_adv_new_url').val(url)
    $('.lbe_adv_new_text').val(text)
    $('.lbe_adv_new_budget').val(budget)

    $('.lbe_adv_new_style').find('option').each(function(){
        $('.lbe_adv_pre_tmp').removeClass($(this).val())
    });
    $('.lbe_adv_pre_tmp').addClass(style)

    $('.lbe_adv_new_style option[value="' + style + '"]').prop('selected', true)

    $('.lbe_adv_pre_tmp span').hide()
    $('.lbe_adv_pre_anchor').text(name)
    $('.lbe_adv_pre_anchor').attr('href', url)
    $('.lbe_adv_pre_text').text(text)

    $('.lbe_adv_new').show()
    $('.lbe_adv_my').hide()
    
    Dajaxice.base.get_cities_adv(get_cities_adv_callback, {'country': country, 'city': city})
    
});

$(document).delegate('.countries_list_adv', 'change', function(){
    id = $(this).val();
    Dajaxice.base.get_cities_adv(get_cities_adv_callback, {'country': id})
});



$(document).delegate('.country_in_card_alt', 'change', function(){
    $('.city_in_card_alt').prop('disabled', true);
    title = $('.city_in_card_alt').attr('title');
    id = $('.country_in_card_alt').val();
    if(id){
        Dajaxice.user_registration.get_cities(get_cities_alt_callback, {'id': id, 'title': title})
    }
});

$(document).delegate('.lbe_adv_new_style', 'change', function(){
    var cl = $(this).val()
    $(this).find('option').each(function(){
        $('.lbe_adv_pre_tmp').removeClass($(this).val())
    });
    $('.lbe_adv_pre_tmp').addClass(cl)
});

$(document).delegate('.lbe_adv_my_btn', 'click', function(){
    $('.lbe_adv_info, .lbe_adv_new').hide()
    $('.lbe_adv_my').show()
});

$(document).delegate('.lbe_adv_back', 'click', function(){
    $('.lbe_adv_my, .lbe_adv_new').hide()
    $('.lbe_adv_info').show()
});

$(document).delegate('.lbe_new_bg_cancel', 'click', function(){
    $('.lbe_adv_new').hide()
    $('.lbe_adv_info').show()
    $('.lbe_adv_bg_new_budget').val('')
});

$(document).delegate('.lbe_new_adv_bg_add', 'click', function(){
    budget = $('.lbe_adv_bg_new_budget').val()
    id = $('.lbe_new_adv_id').val()
    if(!budget.replace(/ /g,'').length){
        $('.lbe_adv_new_bg_budget').css({'border': '1px solid red'})
    }else{
        $('.lbe_adv_new_bg_budget').css({'border': '1px solid #BCBCBC'})
        $('.lbe_adv_new .lbe_load').css({'color': '#333;'}).html('Загрузка...')
        Dajaxice.base.disable_adv_bg(disable_adv_bg_callback, {'budget': budget, 'id': id})
    }
});

function disable_adv_bg_callback(data){
    if(data.status){
        $('.lbe_adv_bg_new_btn').val('Мой заказ')
        $('.lbe_new_adv_id').val(data.id)
        $('.lbe_new_adv_bg_balance').val(data.balance)
        $('.lbe_new_adv_bg_budget').val(data.budget)
        $('.lbe_adv_new .lbe_load').html('')
        $('.lbe_adv_new').hide()
        $('.lbe_adv_info').show()
    }
}


function get_cities_alt_callback(data){
    $('.city_in_card_alt').html('');
    if(data.all == true){
        $('<option value="">' + all + '</option>').appendTo('.city_in_card_alt');
    }
    for(i in data.content) {
        var option = $('<option value="' + data.content[i].key + '">' + data.content[i].name + '</option>').appendTo('.city_in_card_alt');
    }
    $('.city_in_card_alt').prop('disabled', false);
}

function get_lbe_list_callback(data){
    $('.lbe_list').html(data.content)
    $.fancybox.update()
}

function lbe_countries_cities_callback(data){
    $('.lbe_new_target_country').html(data.countries)
    $('.lbe_new_target_city').html(data.cities)
}

function get_cities_adv_callback(data){
    $('.multiselect').html('')
    
    $('.lbe_adv_new_target_country').html(data.countries)

    for(i in data.cities) {
        var selected = data.cities[i].selected === true ? ' selected' : '';
        
        var option = $('<option value="' + data.cities[i].key + '" ' + selected + '>' + data.cities[i].name + '</option>').appendTo('.lbe_adv_new_target_city .multiselect')
    }
    $(".lbe_adv_new_target_city .multiselect").multiselect({ selectedList: 100 })
    $(".lbe_adv_new_target_city .multiselect").multiselect('refresh')
    
}

function get_schedule_part_callback(data){
    $('.schedule_data-' + data.part).attr('id', '1')
    $('.schedule_data-' + data.part).html(data.content)
}

function add_adv_block_callback(data){
    if(data.close){
        $.fancybox.close()
    }else{
        $('.lbe_adv_new .lbe_load').html('')
                    
        if(data.id != 0){
            $tr = $('.lbe_adv_my').find('#lbe_id_' + data.id)
            $prev = $tr.prev()
            $tr.remove()
            $('#my_adv_' + data.id).remove()
            $prev.after(data.content)
        }else{
            $('.lbe_adv_my .lbe_list_tbl').append(data.content)
            $('.lbe_list_empty').html('')
        }
        $('.lbe_adv_new').hide()
        $('.lbe_adv_my, .lbe_adv_my_btn').show()
    }
}

function add_adv_block_code_callback(data){
    if(data.close){
        $.fancybox.close()
    }else{
        $('.lbe_adv_new .lbe_load').html('')
        
        if(data.id != 0){
            $tr = $('.lbe_adv_my').find('#lbe_id_' + data.id)
            $prev = $tr.prev()
            $tr.remove()
            $('#my_adv_' + data.id).remove()
            $prev.after(data.content)
        }else{
            $('.lbe_adv_my .lbe_list_tbl').append(data.content)
            $('.lbe_list_empty').html('')
        }
        $('.lbe_adv_new').hide()
        $('.lbe_adv_my, .lbe_adv_my_btn').show()
    }
}


function get_my_blocks_callback(data){
    $.fancybox(data.content)
    $('.left_banner_editor_bl-adv').show()
    if(data.t != 1 && data.t != 6){
        $('.lbe_adv_my_btn').click()
    }
    $.getScript("/static/base/js/jquery.form.js")
    $.getScript("/static/base/js/jquery.mask.js", function() {
        $('.lbe_adv_new_budget').unmask().mask('00000')
    });
}


function get_film_opinions_callback(data){
    $.fancybox(data.content)
    if(data.show == 1 || data.show == 2){
        $('.opinions_text').click()
    }
}

function get_film_opinions(id, show){
    show = typeof show !== 'undefined' ? show : 0;
    Dajaxice.film.get_film_opinions(get_film_opinions_callback, {'id': id, 'show': show})
}

function get_background_adv_callback(data){
    if(data.status){
        $.fancybox(data.content)
    }
}

function get_background_adv(){
    Dajaxice.base.get_background_adv(get_background_adv_callback, {})
}

$(document).ready(function(){

    $('.schedule_title').click(function(){
        var date = $('.sch_date').val()
        var arr = {'sch_arrow-h': 'sch_arrow-s', 'sch_arrow-s': 'sch_arrow-h'}
        var part = $(this).attr('class').replace('schedule_title ','')
        $child = $(this).find('div')
        var cl = $child.attr('class')
        var add = arr[cl]
        $child.removeClass(cl).addClass(add)
        if(cl == 'sch_arrow-s'){
            var exist = $('.schedule_data-' + part).attr('id')
            if(exist == '0'){
                $('.schedule_data-' + part).html('Загрузка...')
                Dajaxice.base.get_schedule_part(get_schedule_part_callback, {'part': part, 'date': date})
            }
            $('.schedule_data-' + part).show()
        }else{
            $('.schedule_data-' + part).hide()
        }
    });

    $('.flb_link').click(function(){
        var id = $(this).attr('id').replace('flb_id_','')
        if(id){
            Dajaxice.base.adv_adv_click(function(){}, {'id': id})
        }
    });

    $('.flb_adv_link').click(function(){
        var id = $(this).attr('id').replace('flb_id_','')
        if(id){
            Dajaxice.base.adv_adv_click(function(){}, {'id': id})
        }
    });

    $('.left_banner_editor_adv').click(function(){
        Dajaxice.base.get_my_blocks(get_my_blocks_callback, {})
    });

    $('.left_banner_editor').click(function(){
        Dajaxice.base.get_my_blocks(get_my_blocks_callback, {'btype': 4});
    });
    
    $('.lbe_new_add').click(function(){
        var id = $('.lbe_new_id').val()
        var name = $('.lbe_new_name').val()
        var file = $('.lbe_new_file').val()
        var datefrom = $('.lbe_new_datefrom').val()
        var dateto = $('.lbe_new_dateto').val()
        var places = []
        var sites = []
        
        next = true
        if(!name.replace(/ /g,'').length){
            next = false
            $('.lbe_new_name').css({'border': '1px solid red'})
        }else{
            $('.lbe_new_name').css({'border': '1px solid #BCBCBC'})
        }
        if(id == '0'){
            if(!file.replace(/ /g,'').length){
                next = false
                $('.lbe_new_file').css({'border': '1px solid red'})
            }else{
                $('.lbe_new_file').css({'border': '1px solid #BCBCBC'})
            }
        }
        if(!datefrom.replace(/ /g,'').length){
            next = false
            $('.lbe_new_datefrom').css({'border': '1px solid red'})
        }else{
            $('.lbe_new_datefrom').css({'border': '1px solid #BCBCBC'})
        }
        if(!dateto.replace(/ /g,'').length){
            next = false
            $('.lbe_new_dateto').css({'border': '1px solid red'})
        }else{
            $('.lbe_new_dateto').css({'border': '1px solid #BCBCBC'})
        }
        
        $('.lbe_new_sites').each(function(){
            places.push(1)
            if($(this).attr('checked')){
                sites.push($(this).val())
            }
        });
        
        if(places.length){
            if(!sites.length){
                next = false
                $('.lbe_new_sites').each(function(){ $(this).css({'border': '1px solid red'}) })
            }else{
                $('.lbe_new_sites').each(function(){ $(this).css({'border': '1px solid #BCBCBC'}) })
            }
        }
        if(next){
            $('input[name="lbe_upld"]').click()
        }
    });


    $('.op_send').click(function(){
        var val = $('input:radio[name="rate"]:checked').val()
        if(val){
            $('#op_f').submit()
        }else{
            $('#op_f span').effect('highlight')
        }
    });
    
    $("input[name='checker_all']").click(function(){
        var check = $(this).attr('checked') ? true : false
        $("input[name='checker']").each(function(){
            $(this).prop('checked', check)
        });
    });

    $('.gathering_usa').click(function(){
        $('.stat_block_ru').hide();
        $('.stat_block_usa').show();
        $('.gathering_usa').addClass('selected')
        $('.gathering_ru').removeClass('selected')
    });
    $('.gathering_ru').click(function(){
        $('.stat_block_ru').show();
        $('.stat_block_usa').hide();
        $('.gathering_ru').addClass('selected')
        $('.gathering_usa').removeClass('selected')
    });
    $('.review_new').click(function(){
        $("input[name='profile_id']").val('')
        tinyMCE.getInstanceById('id_note').setContent('')
        $("#new_review_title").val('')
        $('#author_names').show()
        $(".organization_txt").show()
        $('#eye_3').prop('checked', true)
        $('#mind_3').prop('checked', true)
        $('#heart_3').prop('checked', true)
        $("#review_id").val('')
    });
    $('.review_edit').click(function(){
        var id = $(this).attr('id')
        var title = $('#title__' + id).text()
        var text = $('#text__' + id).html()
        var rate = $("input[name='author_rate_" + id + "']").val().split('__')
        var user = $("input[name='author_id__" + id + "']").val()
        if(rate[0] == 'eye_0'){
            $('#eye_3').prop('checked', false)
        }else{
            $('#' + rate[0]).prop('checked', true)
        }
        if(rate[1] == 'mind_0'){
            $('#mind_3').prop('checked', false)
        }else{
            $('#' + rate[1]).prop('checked', true)
        }
        if(rate[2] == 'heart_0'){
            $('#heart_3').prop('checked', false)
        }else{
            $('#' + rate[2]).prop('checked', true)
        }
        $("#new_review_title").val(title)
        tinyMCE.getInstanceById('id_note').setContent(text)
        $("#review_id").val(id)
        $("input[name='profile_id']").val(user)
        $('.nick_bl').hide()
        $(".organization_txt").show()
    });

    $('.exist_com').click(function(){
        var id = $(this).attr('id')
        Dajaxice.film.get_exist_com(get_exist_com_callback, {'id': id})
    });
    
    $('.com_add').click(function(){
        var txt = $('#comment_popup_txt').val()
        if(txt.replace(/\s+/g, '')){
            $(this).parent().submit()
        }
    });
    
    
    $('.lets_leave_com').click(function(){
        var id = $(this).attr('id').split('__')
        var ans = 0
        if(id.length == 2){
            ans = id[1]
            id = id[0]
        }else{
            id = id[0]
        }
        var tmp = $(this).attr('href')
        if(tmp != '#answer'){
            ans = 0
        }
        $("input[name='review']").val(id)
        $("input[name='answer']").val(ans)
        $('#comment_popup_txt').val('')
        $.fancybox($('.leave_comment').show());
    });

});

$(document).delegate('.my_adv_messenger', 'click', function(){
    var id = $(this).parents('tr').attr('id')
    var users_arr = []
    var users_ids = []
    $(this).parents('tr').nextAll('tr[id="' + id + '"]').find(".check_all_item").each(function(){
        if($(this).prop('checked')){
            if($.inArray($(this).val(), users_ids)){
                users_ids.push($(this).val())
                users_arr.push({'id': $(this).val(), 'name': $(this).next('a').text()})
            }
        }
    });

    if(users_arr.length){
        $(this).next('.my_adv_messenger_w').html('')
        recipients = ''
        for(i in users_arr){
            recipients += '<span class="recipient_block" id="' + users_arr[i].id + '" title="Удалить">' + users_arr[i].name + ';</span>'
        }
        $('#messanger_nav__new_dialog').click()
        $('.message_recipients').html(recipients);
        $('.message_create').show()
        $('.messanger_nav').hide()
        $.fancybox.open($('#show_messenger').show());
        $.fancybox.update()
        
    }else{
        $(this).next('.my_adv_messenger_w').html('Выберите пользователя!')
    }
});

$(document).delegate('.check_all_next', 'click', function(){
    var check = $(this).attr('checked') ? true : false
    var id = $(this).parents('tr').attr('id')
    $(this).parents('tr').nextAll('tr[id="' + id + '"]').find(".check_all_item").each(function(){
        $(this).prop('checked', check)
    });
});

$(document).delegate('.background_new_add', 'click', function(){

    var id = $('.lbe_adv_new_id').val()
    var name = $('.lbe_adv_new_anchor').val()
    var file = $('.background_new_file').val()
    var budget = $('.lbe_adv_new_budget').val()
    var start = $('.background_new_start').val()
    budget = typeof budget !== 'undefined' ? budget : '0'
    var txt = $('.lbe_adv_new_text').val()
    var style = $('.lbe_adv_new_style option:selected').val()
    var t = $('.lbe_new_t').val()

    var country = $('.lbe_adv_new_target_country option:selected').val()
    $('input[name="background_new_country"]').val(country)
    var city = ''
    $('.lbe_adv_new_target_city .multiselect option:selected').each(function(){
        city += $(this).val() + ';'
    })
    $('input[name="background_new_cities"]').val(city)

    next = true
    if(!name.replace(/ /g,'').length){
        next = false
        $('.lbe_adv_new_anchor').css({'border': '1px solid red'})
    }else{
        $('.lbe_adv_new_anchor').css({'border': '1px solid #BCBCBC'})
    }
    if(!budget.replace(/ /g,'').length){
        next = false
        $('.lbe_adv_new_budget').css({'border': '1px solid red'})
    }else{
        $('.lbe_adv_new_budget').css({'border': '1px solid #BCBCBC'})
    }

    if(id == '0'){
        if(!file.replace(/ /g,'').length){
            next = false
            $('.background_new_file').css({'border': '1px solid red'})
        }else{
            $('.background_new_file').css({'border': '1px solid #BCBCBC'})
        }
    }
    if(t == '1'){
        if(!txt.replace(/ /g,'').length){
            next = false
            $('.lbe_adv_new_text').css({'border': '1px solid red'})
        }else{
            $('.lbe_adv_new_text').css({'border': '1px solid #BCBCBC'})
        }
    }
    if(t == '2' && id == '0'){
        start = new Date(start)
        today = new Date()
        if(start < today){
            $('.background_new_start').css({'border': '1px solid red'})
        }else{
            $('.background_new_start').css({'border': '1px solid #BCBCBC'})
        }
    }

    if(next){
        $('input[name="lbe_upld"]').click()
    }
});

$(document).delegate('input[name="lbe_upld"]', 'click', function(e){
    var $form = $('.lbe_new_form')
    var reset = true
    $form.ajaxForm({
        beforeSend: function() {
            var percentVal = 'Загрузка... 0%';
            $form.find('.lbe_load').css({'color': '#333;'}).html(percentVal);
        },
        uploadProgress: function(event, position, total, percentComplete) {
            var percentVal = 'Загрузка... ' + percentComplete + '%';
            $form.find('.lbe_load').html(percentVal);
        },
        success: function(data){
            $form.find('.lbe_load').html('')

            if(data.error.length){
                $('.lbe_new_error').html(data.error)
            }else{
                $('.lbe_new_error').html('')
                if(data.id != 0){
                    $tr = $('.lbe_list_tbl').find('#lbe_id_' + data.id)
                    $prev = $tr.prev()
                    $tr.remove()
                    $prev.after(data.content)
                }else{
                    $('.lbe_list_tbl').append(data.content)
                    $('.lbe_list_empty').html('')
                }
                $('.lbe_adv_new').hide()
                $('.lbe_adv_my').show()
            }
            if(data.close){
                $.fancybox.close()
            }
        },
    }); 
});


$(document).delegate('.lbe_new_adv_add', 'click', function(){
    var id = $('.lbe_new_adv_id').val()
    var anchor = $('.lbe_adv_new_anchor').val()
    var url = $('.lbe_adv_new_url').val()
    var txt = $('.lbe_adv_new_text').val()
    var budget = $('.lbe_adv_new_budget').val()
    var country = $('.lbe_adv_new_target_country option:selected').val()
    var t = $('.lbe_new_t').val()
    var close = $('input[name="close"]').val()
    var city = []
    $('.lbe_adv_new_target_city .multiselect option:selected').each(function(){
        city.push($(this).val())
    })
    
    var style = $('.lbe_adv_new_style option:selected').val()

    next = true
    if(!anchor.replace(/ /g,'').length){
        next = false
        $('.lbe_adv_new_anchor').css({'border': '1px solid red'})
    }else{
        $('.lbe_adv_new_anchor').css({'border': '1px solid #BCBCBC'})
    }
    if(!url.replace(/ /g,'').length){
        next = false
        $('.lbe_adv_new_url').css({'border': '1px solid red'})
    }else{
        $('.lbe_adv_new_url').css({'border': '1px solid #BCBCBC'})
    }
    if(!txt.replace(/ /g,'').length){
        next = false
        $('.lbe_adv_new_text').css({'border': '1px solid red'})
    }else{
        $('.lbe_adv_new_text').css({'border': '1px solid #BCBCBC'})
    }
    if(!budget.replace(/ /g,'').length){
        next = false
        $('.lbe_adv_new_budget').css({'border': '1px solid red'})
    }else{
        $('.lbe_adv_new_budget').css({'border': '1px solid #BCBCBC'})
    }
    
    if(next){
        $('.lbe_adv_new .lbe_load').css({'color': '#333;'}).html('Загрузка...')
        Dajaxice.base.add_adv_block(add_adv_block_callback, {'id': id, 'anchor': anchor, 'url': url, 'txt': txt, 'budget': budget, 'country': country, 'city': city, 'style': style, 't': t, 'close': close})
    }
});

$(document).delegate('.lbe_new_adv_code_add', 'click', function(){
    var id = $('.lbe_new_adv_code_id').val()
    var anchor = $('.lbe_adv_new_code_anchor').val()
    var txt = $('.lbe_adv_new_code_text').val()
    var t = $('.lbe_new_code_t').val()
    var show = $('.lbe_adv_new_code_show').prop('checked')

    next = true
    if(!anchor.replace(/ /g,'').length){
        next = false
        $('.lbe_adv_new_code_anchor').css({'border': '1px solid red'})
    }else{
        $('.lbe_adv_new_code_anchor').css({'border': '1px solid #BCBCBC'})
    }
    if(!txt.replace(/ /g,'').length){
        next = false
        $('.lbe_adv_new_code_text').css({'border': '1px solid red'})
    }else{
        $('.lbe_adv_new_code_text').css({'border': '1px solid #BCBCBC'})
    }
    
    if(next){
        $('.lbe_adv_code_new .lbe_load').css({'color': '#333;'}).html('Загрузка...')
        Dajaxice.base.add_adv_code_block(add_adv_block_callback, {'id': id, 'anchor': anchor, 'txt': txt, 't': t, 'show': show})
    }
});



$(document).delegate('.lbe_adv_new_anchor', 'focusout', function(){
    $('.lbe_adv_pre_tmp span').hide()
    $('.lbe_adv_pre_anchor').text($(this).val())
});
$(document).delegate('.lbe_adv_new_url', 'focusout', function(){
    $('.lbe_adv_pre_tmp span').hide()
    $('.lbe_adv_pre_anchor').attr('href', $(this).val())
});
$(document).delegate('.lbe_adv_new_text', 'focusout', function(){
    $('.lbe_adv_pre_tmp span').hide()
    $('.lbe_adv_pre_text').text($(this).val())
});
$(document).delegate('.lbe_adv_new_budget', 'focusout', function(){
    var budget = $(this).val()
    var price = $('.lbe_new_adv_price').val()
    var clicks = parseInt(budget / price)
    $('.lbe_adv_new_clicks').html('= кликов: ' + clicks)
});
$(document).delegate('.lbe_new_cancel', 'click', function(){
    lbe_new_clear()
    $('.lbe_list, .lbe_adv_info').show()
    $('.lbe_new, .lbe_adv_new, .lbe_adv_my').hide()
});
$(document).delegate('.lbe_edit_cancel', 'click', function(){
    lbe_new_clear()
    $('.lbe_adv_my').show()
    $('.lbe_adv_new, .lbe_adv_info').hide()
});

$(document).delegate('.lbe_new_btn', 'click', function(){
    lbe_new_clear()
    Dajaxice.user_registration.get_countries_cities_alt(lbe_countries_cities_callback, {'check_all': true})
});

$(document).delegate('.lbe_adv_bg_new_budget', 'focusout', function(){
    var budget = $(this).val()
    var price = $('.lbe_new_adv_price').val()
    var days = parseInt(budget / price)
    $('.lbe_adv_new_days').html('= дней без фона: ' + days)
});

$(document).delegate('.opinions_text', 'click', function(){
    $('.opinions_text_fields').show()
    $('.opinions_list').hide()
    $(this).hide()
    $.fancybox.update()
    $('.otext').focus()
});

$(document).delegate('.opinions_text_cancel_btn', 'click', function(){
    $('.opinions_text_fields').hide()
    $('.opinions_list, .opinions_text').show()
    $.fancybox.update()
});

function send_film_opinion_callback(data){
    if(data.status){
        if(data.content){
            $('.opinions_list').prepend(data.content)
            $('#opinions_empty, .opinions_text_fields').hide()
            $('.opinions_list, .opinions_text').show()
            $('.otext').val('')
            $('#author_names table').remove()
            $.fancybox.update()
        }else{
            $('.opinion_msg').html('Вы уже оставляли отзыв к этому фильму')
        }
    }else{
        $('.opinion_msg').html('Ошибка')
    }
    $('.opinions_text_accept_btn').prop('disabled', false)
}

$(document).delegate('.opinions_text_accept_btn', 'click', function(){
    id = $('.ofilm_id').val()
    txt = $('.otext').val()
    eye = $('input[name="eye"]:checked').val()
    heart = $('input[name="heart"]:checked').val()
    mind = $('input[name="mind"]:checked').val()
    nick = $('input[name="author_nick"]:checked').val()

    eye = typeof eye !== 'undefined' ? eye : 0;
    heart = typeof heart !== 'undefined' ? heart : 0;
    mind = typeof mind !== 'undefined' ? mind : 0;

    if(txt.replace(/\s+/g, '').length){
        $('.opinion_msg').html('')
        $(this).prop('disabled', true)
        Dajaxice.film.send_film_opinion(send_film_opinion_callback, {'id': id, 'txt': txt, 'eye': eye, 'heart': heart, 'mind': mind, 'nick': nick})
    }else{
        $('.opinion_msg').html('Введите текст')
    }
});

$(document).delegate('.opinions_rate_accept_btn', 'click', function(){
    id = $('.ofilm_id').val()
    eye = $('input[name="eye"]:checked').val()
    heart = $('input[name="heart"]:checked').val()
    mind = $('input[name="mind"]:checked').val()
    $('.opinion_msg').html('')
    $(this).prop('disabled', true)
    Dajaxice.film.send_film_rate(function(){}, {'id': id, 'eye': eye, 'heart': heart, 'mind': mind})
    $.fancybox.close()
});

$(document).delegate('.lbe_adv_bg_new_btn', 'click', function(){
    var id = $('.lbe_new_adv_id').val()
    $('.lbe_adv_info').hide()
    $('.lbe_adv_new').show()
    if(id != '0'){
        $('.lbe_adv_balance_bl').show()
        price = $('.lbe_new_adv_price').val()
        balance = $('.lbe_new_adv_bg_balance').val()
        budget = $('.lbe_new_adv_bg_budget').val()
        $('.lbe_adv_bg_new_budget').val(budget)
        $('.lbe_adv_bg_new_balance').html(balance)
        $('.lbe_adv_new_balance_days').html('= дней без фона: ' + parseInt(balance / price))
    }
        
}); 

$(document).delegate('.lbe_adv_new_btn', 'click', function(){
    lbe_new_clear()
    $('.lbe_new_cancel').show()
    $('.lbe_edit_cancel, .lbe_adv_my, .lbe_adv_info').hide()
    Dajaxice.base.get_cities_adv(get_cities_adv_callback, {})
});

$(document).delegate('#persons_top_line a', 'mouseenter', function(){
    $(this).children().show()
});
$(document).delegate('#persons_top_line a', 'mouseleave', function(){
    $(this).children().hide()
});


$(document).delegate('.leave_com', 'click', function(){
    var id = $(this).attr('id').split('__')
    var ans = 0
    if(id.length == 2){
        ans = id[1]
        id = id[0]
    }else{
        id = id[0]
    }
    var tmp = $(this).attr('href')
    if(tmp != '#answer'){
        ans = 0
    }
    $("input[name='review']").val(id)
    $("input[name='answer']").val(ans)
    $('#comment_popup_txt').val('')
    $.fancybox.open($('.comment_popup').show())
});
    
function get_exist_com_callback(data){
    if(data.status == true){
        var txt = ''
        for(i in data.content){
            var ans = data.content[i].user
            if(data.content[i].answer){
                var ans = data.content[i].user + ' <span style="color:#29A329;">ответ для</span> ' + data.content[i].answer
            }
            txt += '<div class="message_block"><div class="message_head"><b>' + ans + '</b> <em>' + data.content[i].date + '</em></div><div class="message_text">' + data.content[i].comment + '<div style="text-align: right;"><a href="#answer" class="leave_com" id="' + data.id + '__' + data.content[i].id + '">Ответить</a></div></div></div>'
        }
        $.fancybox.open($('.comments_popup').show().html(txt));
        $('.comments_popup').append('<br /><a href="#" class="leave_com" id="' + data.id + '">Добавить комментарий</a>');
    }
}

function obj_edit(el){
    var val = $(el).attr('class').split(' ')
    $(el).hide()
    var show_el = '.' + val[0] + '_fields'
    $(show_el).show()
}
function obj_cancel(el){
    var val = $(el).attr('class').replace('_cancel_btn','')
    var hide_el = '.' + val + '_fields'
    $(hide_el).hide()
    $('.' + val).show()
    $('#film_trailers, #film_slides').show()
}

function show_likes(data){
    $('.count_likes').html('').html(data.count_likes)
    $('.count_dislikes').html('').html(data.count_dislikes)
    $('.likes_home').html('').html(data.likes_home)
    $('.likes_cinema').html('').html(data.likes_cinema)
    $('.likes_recommend').html('').html(data.likes_recommend)
    $('.dislikes_seen').html('').html(data.dislikes_seen)
    $('.dislikes_recommend').html('').html(data.dislikes_recommend)
    if(data.cancel){
        $('.subs').html('<div class="subscription_release subs_btn">Сообщите мне о сеансах в моём городе</div>')
        $('.subs_btn').css({'background-color': '#F0D1B2'})
    }
    if(data.email_block){
        $.fancybox(data.email_block)
    }else{
        $.fancybox.close()
    }
    $(".like_list__options, .dislike_list__options").attr('id', '')
}

function show_likes2(data){
    $('#count_l_' + data.id).html('').html(data.count_likes)
    $('#count_d_' + data.id).html('').html(data.count_dislikes)
    $('#like_' + data.id).find('.likes_home').html('').html(data.likes_home)
    $('#like_' + data.id).find('.likes_cinema').html('').html(data.likes_cinema)
    $('#like_' + data.id).find('.likes_recommend').html('').html(data.likes_recommend)
    $('#dislike_' + data.id).find('.dislikes_seen').html('').html(data.dislikes_seen)
    $('#dislike_' + data.id).find('.dislikes_recommend').html('').html(data.dislikes_recommend)
    if(data.cancel){
        $('.subs').html('<div class="subscription_release subs_btn">Сообщите мне о сеансах в моём городе</div>')
        $('.subs_btn').css({'background-color': '#F0D1B2'})
    }
    if(data.email_block){
        $.fancybox(data.email_block)
    }else{
        $.fancybox.close()
    }
    $(".like_list__options, .dislike_list__options").attr('id', '')
}

function get_film_callback(data){
    if(data.status){
        $('#kid').html('').html(data.id)
        $('.loader').hide()
        $('#loader').html('')
        $('#poster').html('').html(data.posters)
        show_likes(data)
        $('#film_name_in_bar').html('').html(data.name_ru)
        $('#film_name').html('').html(data.name_ru + ' <span class="film_year">(' + data.year + ')</span><p>' + data.name_en +'</p>')

        $('#film_details').html('').html(data.details)
        $('#film_genre').html('').html(data.genre)
        $('#persons_top_line').html('').html(data.top_line)
        $('#film_description').html('').html(data.description_cut + ' <a id="descript" href="#in_descript">[Подробнее]</a>')
        $('#age_limit').html('').html(data.limits)
        $('#film_slides').html('').html(data.slides.slice(0, 3))
        $('.subs').html('')
        if(data.subscriptions_accept){
            if(data.subscription == true){
                $('.subs').html('<div class="subscription_release subs_btn" id="cancel_subs">Отменить уведомление о сеансах этого фильма</div>')
                $('.subs_btn').css({'background-color': '#E6E6E6'})
            }else{
                $('.subs').html('<div class="subscription_release subs_btn">Сообщите мне о сеансах в моём городе</div>')
                $('.subs_btn').css({'background-color': '#F0D1B2'})
            }
        }
        $('.subs').attr('id', data.id)

        $('#film_bottom_details #reviews').html('').html(data.reviews)
        $('#film_bottom_details #opinions').html('').html(data.opinions)
        $('#film_bottom_details #soundcopies').html('').html(data.copies)
        $('#film_bottom_details #bx_office').html('').html(data.boxoffice)
        $('#film_bottom_details #distribs').html('').html(data.distributors)
        $('#film_bottom_details #budget').html('').html(data.budget)
        $('#film_bottom_details #release_dt').html('').html(data.release)
        
        $('.film_under_poster').html('').html(data.m_rate)
        //$('.subme_bl').html('').html(data.subscribe_me)
        
        $('#in_descript').hide().html('').html(data.description + data.directors + data.actors + data.other_person)

        $('#film_trailers').html('').html(data.trailers)
        $('iframe').attr({'width': '250px', 'height': '150px'})
        $('object').attr({'width': '250px', 'height': '150px'})
        $('embed').attr({'width': '250px', 'height': '150px'})

        if(data.player){
            $('#player').html('').html(data.player)
        }

        $('#subscribe_info').attr('class', 'rate_color_' + data.rate)
        $('.pen_rate b').attr('title', data.rate_text)
        $('.pen_rate b').html(data.rate)
        $('.triangle').attr('style', data.rate_color)
        
        $('#film_info').show()
        
        if(RELEASE_SUBSCRIBE_ME){
            $('.subs_btn').html('Загрузка...')
            Dajaxice.user_registration.subscription(subscription_release_callback, {'id': data.id, 'cancel': ''})
        }
    }else{
        $('#film_name').html('Ошибка')
    }
}

function get_torrent_file_callback(data){
    if(data.paid){
        window.location = '/torrent/get/' + data.id + '/'
        /*$.fancybox.close()*/
    }else{
        $.fancybox(data.content)
    }
}

function get_torrent_file(id, pay){
    pay = typeof pay !== 'undefined' ? pay : false;
    Dajaxice.film.get_torrent_file(get_torrent_file_callback, {'id': id, 'pay': pay})
}

function get_film(id, val){
    val = typeof val !== 'undefined' ? val : 0;
    $('.release_film').css({'background-color': 'rgba(255,255,255,0.6)'})
    $('#release_film_id_' + id).css({'background-color': '#FFF'})
    $('#loader').html('Загрузка...')
    $('.loader').css({'display': 'inline-block'})
    $('#film_info').hide()
    Dajaxice.release_parser.get_film(get_film_callback, {'id': id, 'val': val})

    var scroll_to = $('.loader').offset().top - 150
    $(document).scrollTop(scroll_to)
}

function get_film_schedule_callback(data){
    $('#schedules').html('')
    if(data.status == 'True'){
        content = data.schedules
        $('#schedules').html('<select id="select_schedules"></select><span id="schedules_time"></span>')
        for(i in content){
            $('#select_schedules').append('<option value="' + content[i].times + '">' + content[i].dates + '</option>')
            if(i == 0){
                $('#schedules_time').html('<b>' + content[i].times + '</b>')
            }
        }

        var tickets = ''
        if(data.kinohod_tickets.length){
            tickets += '<div class="kinohod_tickets_btn">' + data.kinohod_tickets + '</div>'
        }
        if(data.rambler_tickets.length){
            var cl = tickets.length === 0 ? ' tickets_btn_top' : '';
            tickets += '<div class="rambler_tickets_btn' + cl + '">' + data.rambler_tickets + '</div>'
        }
        $('.tickets_info').html(tickets)
        if(data.kinohod_tickets.length){
            $.getScript("http://load.kinohod.ru/static/js/widget/v4/boxoffice.js?apikey=" + data.kinohod_key)
        }
        if(data.rambler_tickets.length){
            $.getScript("http://s2.kassa.rl0.ru/widget/js/ticketmanager.js")
        }
    }else{
        $('#schedules').append('Ошибка');
    }
}

function watch_at_home(id){
    $('.watch_at_home_id').val(id)
    $.fancybox($('.film_quality').show())
}

$(document).ready(function(){
    $('.watch_at_home_btn').click(function(){
        var q = $('.watch_at_home_quality option:selected').val()
        var id = $('.watch_at_home_id').val()
        Dajaxice.release_parser.likes(show_likes2, {'take_eval': 'Хочу посмотреть дома', 'kid': id, 'email': '', 'quality': q})
    });

    $(".review_rate_details_show").mouseover(function(){
        $(this).parent().find('.review_rate_details').show()
    });
    $(".review_rate_details_show").mouseout(function(){
        $(this).parent().find('.review_rate_details').hide()
    });


    $('.film_cinemas_schedules').on('change', function(){
        var cinema = $(this).children(":selected").val()
        get_film_schedule(film_id_schedules, cinema, 2)
    });
    
    $('.film_cinemas_schedules_v2').on('change', function(){
        var id = $(this).attr('id').replace('select__','')
        var times = $(this).children(":selected").val()
        $('#times__' + id).html('<b>' + times + '</b>')
    });

    $('.film_cinemas_schedules_v3').on('change', function(){
        var id = $(this).attr('id').replace('select__','')
        var val = $(this).children(":selected").val()
        $('#times__' + id + ' span').hide()
        $('.film_sch_bl_' + id + '_' + val).show()
    });

    $('.film_cinemas_schedules_v4').on('change', function(){
        var id = $(this).attr('id').replace('select__','')
        var val = $(this).children(":selected").val()
        var val2 = $('#select__' + id + '__' + val).children(":first").prop('selected', true).val()
        $('#dates__' + id + ' select, #times__' + id + ' span').hide()
        $('#select__' + id + '__' + val).show()
        $('#times__' + id + '__' + val).show()
        $('#times__' + id + '__' + val + '__' + val2).show()
    });

    $('.film_cinemas_schedules_v5').on('change', function(){
        var id_orig = $(this).attr('id')
        var id = id_orig.split('__')[1]
        var val = $(this).children(":selected").val()
        $('#times__' + id + ' span').hide()
        $('#' + id_orig.replace('select', 'times')).show()
        $('#' + id_orig.replace('select', 'times') + '__' + val).show()
    });

    $(".like").click(function(){
        var par = $(this).parents("#film_poster")
        par.find(".like_list__options").toggle()
        par.find(".dislike_list__options").hide()
    });
    $(".dislike").click(function(){
        var par = $(this).parents("#film_poster")
        par.find(".dislike_list__options").toggle()
        par.find(".like_list__options").hide()
    });

    $(".like_list__options, .dislike_list__options").click(function(){
        var disable = $(this).attr('id')
        disable = typeof disable !== 'undefined' ? disable : '';
        if(disable != 'disable'){
            title = $(this).attr("title")
            var id = $(this).parent().attr('id')
            if(id){
                id = id.replace('dislike_','').replace('like_','')
                func = show_likes2
            }else{
                id = $('#kid').text()
                func = show_likes
            }
            $(".like_list__options, .dislike_list__options").attr('id', 'disable')
            Dajaxice.release_parser.likes(func, {'take_eval': title, 'kid': id})
        }
        var par = $(this).parents("#film_poster")
        par.find(".like_list__options, .dislike_list__options").hide()
    });

    $('#show_relations').prop('disabled', true)
    $("#nof_data").on("change", function(){
        id = $(this).children(":selected").attr("id")
        $("#info_" + id).show().siblings().hide()
    });

    $('#rel').prop('disabled', true)
    $('#kid_sid').prop('disabled', true)
    $('#ignore').prop('disabled', true)
    $(".radio_checker").on("change", function(){
        var value =  $(this).attr("id").split(' @ ')[0]
        $('#get_data_name').attr('value', value)
        $('#rel').prop('disabled', true)
        $('#kid_sid').prop('disabled', true)
        $('#ignore').prop('disabled', false)
        $('#newcinema').prop('disabled', false)
        $('#data_select').html('')
        var option = $('<option value="">пусто</option>').appendTo('#data_select')
    });

    //navigation_bar
    $('#cities2').click(function(){
        $("#cities_inline").toggle("slide", {direction:"left"})
        $('#cinemas').css({'background-color': 'rgba(255,255,255,0.6)'})
        $('#cities').css({'background-color': 'rgba(255,255,255,0.8)'})
        $("#cinemas_inline").hide()
    });
    //navigation_bar
    $('#cinemas2').click(function(){
        $("#cinemas_inline").toggle("slide", {direction:"left"})
        $('#cinemas').css({'background-color': 'rgba(255,255,255,0.8)'})
        $('#cities').css({'background-color': 'rgba(255,255,255,0.6)'})
        $("#cities_inline").hide();
    });

});


function get_film_schedule(fkid, ckid){
    $('#film_schedule').html('')
    $('#schedules').html('').html('Загрузка сеансов...');
    Dajaxice.release_parser.get_film_schedule(get_film_schedule_callback, {'fkid': fkid, 'ckid': ckid})
}

function save_city_choice(city){
    Dajaxice.release_parser.save_city_choice(function(){}, {'city': city})
}

function get_sub_country_callback(data){
    $('#sub_city').html('');
    if(data.status == true){
        for(i in data.content) {
            var option = $('<option value="' + data.content[i].key + '">' + data.content[i].name + '</option>').appendTo('#sub_city');
        }
    }
}
function get_sub_country_callback2(data){
    $('#sub_city2').html('');
    if(data.status == true){
        for(i in data.content) {
            var option = $('<option value="' + data.content[i].key + '">' + data.content[i].name + '</option>').appendTo('#sub_city2');
        }
    }
}

function buy_ticket_callback(data){
    if(data.result){
	    $.fancybox.open({
             href: data.result,
             type: 'iframe',
        });
    }
}

$(document).delegate('#email_likes_btn', 'click', function(){
    email = $('#email_likes').val()
    film = $('#film_likes').val()
    like = $('#eval_likes').val()
    q = $('#tquality').val()
    if(IsEmail(email)){
        $('#email_likes_warnign').html('')
        $(this).prop('disabled', true)
        func = typeof $('#kid') !== 'undefined' ? show_likes : show_likes2
        Dajaxice.release_parser.likes(func, {'take_eval': like, 'kid': film, 'email': email, 'quality': q})
    }else{
        $('#email_likes_warnign').html('Неверно введен E-Mail адрес!')
    }
});

$(document).delegate('#sub_country', 'change', function(){
    id = $(this).children(":selected").val()
    Dajaxice.user_registration.get_cities(get_sub_country_callback, {'id': id})
});

$(document).delegate('#sub_country2', 'change', function(){
    id = $(this).children(":selected").val()
    Dajaxice.user_registration.get_cities(get_sub_country_callback2, {'id': id})
});

$(document).delegate('#schedules_time a', 'click', function(){
    id = $(this).attr('id');
    Dajaxice.release_parser.buy_ticket(buy_ticket_callback, {'id': id})
})

$(document).delegate('#select_schedules', 'change', function(){
    var val = $(this).val();
    $('#schedules_time').html('<b>' + val + '</b>')

})

$(document).delegate('#sub_button', 'click', function(){
    var id = $('.subs').attr('id')
    var city = $('#sub_city').children(":selected").val()
    var email = $('input:radio[name="sub_emails"]:checked').val()
    if(email){}else{
        email = $('#sub_email').val()
        if(email){}else{
            $("#sub_email_warnign").html('').html(' Обязательное поле')
        }
    }
    if(city || email){
        Dajaxice.user_registration.subscription(subscription_release_callback, {'id': id, 'cancel': '', 'email': email, 'city': city})
    }
});

$(document).delegate('#sub_button_topic', 'click', function(){
    var id = $('.subs').attr('id')
    var email = $('input:radio[name="sub_emails"]:checked').val()
    if(email.length){
        Dajaxice.user_registration.subscription_topics(subscription_topics_callback, {'id': id, 'email': email})
    }
});

$(document).delegate('.subscription_topic', 'click', function(){
    var id = $(this).attr('alt')
    id = typeof id !== 'undefined' ? id : $('.subs').attr('id')
    Dajaxice.user_registration.subscription_topics(subscription_topics_callback, {'id': id})
});

function subscription_topics_callback(data){
    if(data.status){
        if(data.email == false){
            if(data.emails == false){
                $("#inline3 #sub_email, #inline3 #sub_email_warnign").remove()
                $("#inline3 #sub_auth_btn, #inline3 #sub_email_note").remove()
                $("#inline3 #sub_e").append('<input type="text" id="sub_email" name="email_auth" /><span id="sub_email_warnign"></span>')
                $("#inline3 #sub_e").append('<input type="submit" id="sub_auth_btn" value="ОК" />')
                $("#inline3 #sub_e").append('<p id="sub_email_note">Введите Ваш e-mail, тогда мы оповестим Вас о выходе фильма в сети.</p>')
            }else{
                $('#inline3').append('Оповещать на: <br />')
                for(var i=0; i<data.emails.length; i++){
                    var checked = i==0 ? 'checked' : ''
                    var value = data.emails[i]
                    $('#inline3').append('<input type="radio" name="sub_emails" group="emails" value="' + value + '"' + checked + '/> ' + value + '<br />')
                }
                $("#inline3").append('<br /> <input type="button" id="sub_button_topic" value="Сохранить" />')
            }
            $("#various3").fancybox().click()
        }else{
            $.fancybox.close()
        }
    }else{
        if(data.reload){ location.reload() }
        var topic = $('.subscription_topic').attr('rel')
        topic = typeof id !== 'undefined' ? topic : ''
        if(topic.length){
            $('.subscription_topic').click()
        }
    }
}

function subscription_trigger(data){
    if(data.sub_status == true){
        $('.subs').html('<div class="subscription_release subs_btn" id="cancel_subs">Отменить уведомление о сеансах этого фильма</div>')
        $('.subs_btn').css({'background-color': '#E6E6E6'})
        $.fancybox.close()
    }else{
        $('.subs').html('<div class="subscription_release subs_btn">Сообщите мне о сеансах в моём городе</div>')
        $('.subs_btn').css({'background-color': '#F0D1B2'})
        if(!data.like){
            $('.likes_cinema').html('0')
        }
    }
}

function subscription_release_callback(data){
    if(data.status){
        if(data.email == true){
            subscription_trigger(data)
                    
            if(RELEASE_SUBSCRIBE_ME){
                window.location = window.location.href.split("?")[0]
            }
        }else{
            if(data.country){
                if(data.emails != false){
                    $("#inline3").html('')
                }
                
                $("#inline3").append('<h3>Укажите Ваше местоположение</h3><br />Страна: <select id="sub_country"></select>')
                for(i in data.countries){
                    var selected = data.countries[i].key == data.country ? 'selected' : ''
                    $('<option value="' + data.countries[i].key + '" ' + selected + '>' + data.countries[i].name + '</option>').appendTo('#sub_country')
                }
                $("#inline3").append(' Город: <select id="sub_city"></select>')
                for(i in data.cities) {
                    var selected = data.cities[i].key == data.city ? 'selected' : ''
                    $('<option value="' + data.cities[i].key + '" ' + selected + '>' + data.cities[i].name + '</option>').appendTo('#sub_city')
                }
                $("#inline3").append('<br /><br />')
                $("#inline3").append(' <input type="button" id="sub_button" value="Сохранить" />')

            }

            if(!data.country && data.flag == false){
                var f = $('#sub_e')
                $("#inline3").html('').html(f)
                
                if(data.emails == false){
                    $("#inline3 #sub_email, #inline3 #sub_email_warnign").remove()
                    $("#inline3 #sub_auth_btn, #inline3 #sub_email_note").remove()
                    $("#inline3 #sub_e").append('<input type="text" id="sub_email" name="email_auth" /><span id="sub_email_warnign"></span>')
                    $("#inline3 #sub_e").append('<input type="submit" id="sub_auth_btn" value="ОК" />')
                    $("#inline3 #sub_e").append('<p id="sub_email_note">Введите Ваш e-mail, тогда мы оповестим Вас о выходе релиза.</p>')
                }else{
                    $('#inline3').append('Оповещать на: <br />')
                    for(var i=0; i<data.emails.length; i++){
                        var checked = i==0 ? 'checked' : ''
                        var value = data.emails[i]
                        $('#inline3').append('<input type="radio" name="sub_emails" group="emails" value="' + value + '"' + checked + '/> ' + value + '<br />')
                    }
                    $("#inline3").append('<br /> <input type="button" id="sub_button" value="Сохранить" />')
                }
            }
            $("#various3").fancybox()
            $("#various3").click()
        }

    }else{
        if(data.reload){ location.reload() }
    }
}

$(document).delegate('.subscription_release', 'click', function(){
    var cancel = $(this).attr('id')
    cancel = typeof cancel !== 'undefined' ? cancel : '';
    var release = $('.subs').attr('id')
    $('.subs_btn').html('Загрузка...')
    Dajaxice.user_registration.subscription(subscription_release_callback, {'id': release, 'cancel': cancel})
});


function checker_func(value){
    $('#get_data_name').val(value)
}

/* end Film */

/* begin Person */
$(document).ready(function(){
    $('.person_page_bg_accept_btn').click(function(){
        var url = $('input[name="person_page_bg_url"]').val()
        var file = $('input[name="person_page_bg_file"]').val()
        var err = ''

        if(url.replace(/ /g,'').length){ 
            if(file.replace(/ /g,'').length){ 
                $(this).parent().submit()
            }else{
                err += 'Прикрепите файл.'
            }
        }else{
            err += 'Укажите URL. '
        }
        if(err){
            $('.person_page_bg_fields span').html(err + '<br />')
        }
    
    });

    $('.person_name_accept_btn').click(function(){
        var id = $("input[name='person_id']").val();
        var name = $(".person_name_field").val();
        var en = $(".person_name_en_field").val();
        var par = $(".person_par_name_field").val();
        en = typeof en !== 'undefined' ? en : '';
        par = typeof par !== 'undefined' ? par : '';
        $('.person_name_fields').hide();
        $('.person_name').html(name).show();
        $('.person_en_name').html(en).show();
        Dajaxice.person.names(person_names_callback, {'id': id, 'name': name, 'par': par, 'en': en});
    });
    
    $('.person_country_city_accept_btn').click(function(){
        var id = $("input[name='person_id']").val();
        var country = $(".country_in_card option:selected").val();
        var country_name = $(".country_in_card option:selected").text();
        var city = $(".city_in_card option:selected").val();
        var city_name = $(".city_in_card  option:selected").text();
        $('.person_country_city_fields').hide();
        $('.person_country_city').html(country_name + ', ' + city_name).show();
        Dajaxice.person.country_city(person_country_city_callback, {'id': id, 'country': country, 'city': city});
    });

    $('.person_gender_accept_btn').click(function(){
        var id = $("input[name='person_id']").val()
        var gender = $("select[name='person_gender'] option:selected").val()
        var domain = window.location.host
        if(gender > 0){
            $('.person_gender').html($("select[name='person_gender'] option:selected").text()).show()
            var txt = gender == 1 ? 'Родился: ' : 'Родилась: '
            if(domain == 'letsgetrhythm.com.au' || window.location.host == 'vladaalfimovdesign.com.au'){
                txt = 'Born: '
            }
            $('.born_txt').text(txt)
        }else{
            var txt = 'Дата рождения: '
            var s = 'пол'
            if(domain == 'letsgetrhythm.com.au' || window.location.host == 'vladaalfimovdesign.com.au'){
                txt = 'DOB: '
                s = 'sex'
            }
            $('.person_gender').html('<span style="font-weight: normal;">' + s + '</span>').show()
            $('.born_txt').text(txt)
        }
        $('.person_gender_fields').hide()
        Dajaxice.person.gender(function(){}, {'id': id, 'gender': gender})
    });
    
    $('.person_borned_accept_btn').click(function(){
        var id = $("input[name='person_id']").val()
        var day = $(".person_born_day option:selected").val()
        var month = $(".person_born_month option:selected").val()
        var year = $(".person_born_year option:selected").val()
        $('.person_borned_fields').hide()
        Dajaxice.person.borned(person_borned_callback, {'id': id, 'year': year, 'month': month, 'day': day})
    });
    
    $('.person_nick_accept_btn').click(function(){
        var id = $("input[name='person_id']").val()
        var nick = $(".person_nickname").val()
        if(nick.replace(/\s+/g, '').length){
            $('.person_nick_err').hide()
            Dajaxice.person.nickname(person_nickname_callback, {'id': id, 'nick': nick})
        }else{
            $('.person_nick_err').show()
        }
    });
    
    $('.person_email_accept_btn').click(function(){
        var id = $("input[name='person_id']").val()
        var email = $(".person_email option:selected").val()
        $('.person_email_fields').hide()
        $('.person_email').html(email).show()
        Dajaxice.person.email(function(){}, {'id': id, 'email': email})
    });
    
    $('.person_show_profile_accept_btn').click(function(){
        var id = $("input[name='person_id']").val()
        var show = $(".show_profile option:selected").val()
        $('.person_show_profile_fields').hide()
        $('.person_show_profile').html($(".show_profile option:selected").text()).show()
        Dajaxice.person.show_profile(function(){}, {'id': id, 'show': show})
    });
    
    $('.person_phone_accept_btn').click(function(){
        var id = $("input[name='person_id']").val()
        var show = $(".show_phone option:selected").val()
        var show_txt = $(".show_phone option:selected").text()
        var num = $('.person_phone_num').val()
        Dajaxice.person.set_phone(function(){}, {'id': id, 'show': show, 'num': num})
        $('.person_phone').html(num + ' (' + show_txt + ')').show()
        $('.person_phone_fields').hide()
    });
    
    $('.artist_type_accept_btn').click(function(){
        var id = $("input[name='person_id']").val()
        var atype = $(".artist_type_field option:selected").val()
        var atype_txt = $(".artist_type_field option:selected").text()
        Dajaxice.person.set_artist_type(function(){}, {'id': id, 'atype': atype})
        $('.artist_type').html(atype_txt).show()
        $('.artist_type_fields').hide()
        if(atype=='1'){
            $('.person_gender').show()
            $('.person_born_fields b').html('дата рождения:')
        }else{
            $('.person_gender').hide()
            $('.person_born_fields b').html('дата основания:')
        }
    });
    
});

function person_nickname_callback(data){
    if(data.status){
        if(data.nick_err){
            $('.person_nick_err').show()
        }else{
            $('.person_nick_err').hide()
            if(data.nick_exist){
                $('.person_nick_exist').show()
            }else{
                $('.person_nick').html(data.content)
                $('.person_nick_fields, .person_nick_exist').hide()
                $('.person_nick').show()
            }
        }
    }
}

function person_names_callback(data){
    if(data.status){
        $('#user_full_name').text(data.content);
        if(data.status == 'error'){
            alert(data.content)
        }
    }
}
function person_country_city_callback(data){
    if(data.status){
        $('.upper-menu__control-links__city').text(data.content);
    }
}
function person_borned_callback(data){
    if(data.status){
        if(data.content.length){
            $('.person_borned').html(data.content).show();
        }else{
            $('.person_borned').html('<span style="color: red;">неверная дата</span>').show();
        }
    }
}
/* end Person */


/* begin Post */
function bpost_comments_clear(parent){
    parent.find('#char_count').html('')
    parent.find('.comments_block-new textarea').val('')
    parent.find('.comments_block-new-answer').val('0')
    parent.find('.comments_block-add_link').css({'display': 'inline'})
    parent.find('.comments_block-content').show()
    parent.find('.comments_block-new').hide()
}
function get_bpost_comments(id){
    $('.loader').show()
    Dajaxice.user_registration.bpost_comments(bpost_comments_callback, {'id': id})
}
function bpost_comments_callback(data){
    $('.loader').hide()
    if(data.status){
        if(data.parent){
            $parent = $('#' + data.parent)
        }else{
            $parent = $('.comments_block')
        }
        
        if(data.error){
            $parent.find('.comments_subscribe-bl').show()
            $parent.find('#comments_subscribe-msg').html(data.content)
        }else{
            var html = 'Нет'
            if(data.content.length){
                html = data.content
            }
            $parent.find('.comments_block-content').html(html)
            bpost_comments_clear($parent)
        }
    } 
    $parent.find('.comments_block-new-btn, .comments_block-new-cancel').prop('disabled', false)
}

function comments_add(el, answer){
    $parent = $(el).parents('.comments_block')
    answer = typeof answer !== 'undefined' ? answer : '0'
    $parent.find('.comments_block-new-answer').val(answer)
    $parent.find('.comments_block-content, .comments_block-add_link').hide()
    $parent.find('.comments_block-new').show()
}

function create_question_callback(data){
    $.fancybox(data.content)
}

$(document).ready(function(){
    $('.booking-add-article').click(function(){
        $('input[name="news_title"]').val('')
        $('input[name="edit"]').val(0)
        tinyMCE.getInstanceById('id_text').setContent('')
        $('.booking-schedules').hide()
        $('.booking-add-article-block').show()
    });
    $('.booking-article-edit-cancel').click(function(){
        $('.booking-schedules').show()
        $('.booking-add-article-block').hide()
    });

    $('.budget_open').click(function(){
        var m_id = $(this).attr('id')
        var id = $(this).parents('tr').find('input[name="checker"]').val()
        Dajaxice.imiagroup.budget_open(budget_open_callback, {'id': id, 'member': m_id})
    });

    $('.create_question').click(function(){
        Dajaxice.imiagroup.create_question(create_question_callback, {})
    });

    $('.create_answer').click(function(){
        Dajaxice.imiagroup.create_answer(create_question_callback, {})
    });

    $('.comments_block-new-cancel').click(function(){
        $parent = $(this).parents('.comments_block')
        bpost_comments_clear($parent)
    });

    $('.comments_block-new-btn').click(function(){
        $parent = $(this).parents('.comments_block')
        var id = $parent.find('.comments_block-id').val()
        var answer = $parent.find('.comments_block-new-answer').val()
        var text = $parent.find('.comments_block-new textarea').val()
        var notify = $parent.find('.comments_subscribe').prop('checked')
        var email_exist = $parent.find('#comments_subscribe_form-email').attr('email-exist')
        var email = ''

        if(text.replace(/ /g,'').length){
            next = true
            if(notify && email_exist == '0'){
                email = $parent.find('#comments_subscribe_form-email').val()
                if(!IsEmail(email)){
                    $parent.find('.comments_subscribe-bl').show()
                    $parent.find('#comments_subscribe-msg').html('Введите E-Mail правильно!')
                    next = false
                }
            }

            if(next){
                $parent.find('.comments_block-new-btn, .comments_block-new-cancel').prop('disabled', true)
                $parent.find('.comments_block-new .loader').css({'display': 'inline-block', 'margin-top': '5px'})
                $parent.find('.comments_block-new textarea').css({'border': '1px solid #BCBCBC'})
                Dajaxice.user_registration.bpost_send_comment(bpost_comments_callback, {'id': id, 'text': text, 'answer': answer, 'email': email, 'notify': notify, 'parent': $parent.attr('id')})
            }
        }else{
             $parent.find('.comments_block-new textarea').css({'border': '1px solid red'})
        }

    });

    $('.art-menu__li a').click(function(){
        id = $(this).attr('id').replace('bottom_menu__','')
        if(id.length){
            $.cookie("openItem", id, { expires: 7, path: "/"})
        }
    });

    $('.g_photo_el').hover(
        function(){ 
            $(this).find('.g_photo_del, .g_photo_description, .g_photo_edit').show();
            $(this).addClass('g_shadow')
        },
        function(){ 
            $(this).find('.g_photo_del, .g_photo_description, .g_photo_edit').hide()
            $(this).removeClass('g_shadow')
        }
    );
    
    $('.post_edit_cancel').click(function(){
        $('.article').show()
        $('.post_block').hide()
    });
    

    $('.org_addmenu').click(function(){
        var menu_id = $(this).attr('id')
        var id = $('.org_addmenu_title').attr('id')
        var title = $('.org_addmenu_title').val()
        var private = $('.org_addmenu_private').prop('checked')
        private = typeof private !== 'undefined' ? private : false
        $('.left_banner').show()
        if(menu_id.length && title.length == 0){
            if(confirm("All Articles And Menu Items Related To This Menu Will Be Removed. Continue?")) {
                Dajaxice.organizations.org_add_menu(org_add_menu_callback, {'id': id, 'title': title, 'menu_id': menu_id, 'private': private})
            }else{
                $('.org_addmenu_bl_fields').hide()
            }
        }else{
            Dajaxice.organizations.org_add_menu(org_add_menu_callback, {'id': id, 'title': title, 'menu_id': menu_id, 'private': private})
        }
    });



    $('.booker-exist-cities').on('change', function(){
        var id = $(this).children(":selected").val()
        $('.booker-exist-cinemas-bl').hide()
        $('.booker-exist-cinemas #booker-cinemas-' + id).show()
    });

    $('.booker-selected-cities').on('change', function(){
        var id = $(this).children(":selected").val()
        $('.booker-selected-cinemas-bl').hide()
        $('.booker-selected-cinemas #booker-cinemas-' + id).show()
    });
    

});


$(document).delegate('.del_task', 'click', function(){
    var arr = []
    $('input[name="accept_task"]:checked').each(function(){
        arr.push($(this).val())
    })
    if(arr.length){
        if(confirm("Are You Sure?")){
            Dajaxice.imiagroup.del_tasks(false, {'arr': arr})
            for(i in arr){
                $('#tr_' + arr[i]).remove()
            }
        }
    }
});



$(document).delegate('.add_new_task', 'click', function(){
    $('.new_task_form').find('input[name="details"]').val('')
    $('.new_task_form').find('input[name="date"]').val('')
    $('.new_task_form').find('input[name="edt"]').val('0')
    $('.new_task_form').show();
    $('#future_tasks').hide();
});

$(document).delegate('.task_txt_edit', 'click', function(){
    var $parent = $(this).parents('tr')
    var id = $parent.attr('id').replace('tr_','')
    var date = $parent.find('#tsk_date').text().split('.')
    var text = $parent.find('#tsk_text').text()
    var txt = $(this).text()
    $('.new_task_form').find('input[name="details"]').val(txt)
    $('.new_task_form').find('textarea[name="text"]').val(text)
    $('.new_task_form').find('input[name="date"]').val(date[2] + '-' + date[1] + '-' + date[0])
    $('.new_task_form').find('input[name="edt"]').val(id)
    $('.new_task_form').show();
    $('#future_tasks').hide();
});

$(document).delegate('.new_task_save', 'click', function(){
    var $parent = $('.new_task_form')
    var id = $parent.find('input[name="project"]').val()
    var stage = $parent.find('input[name="stage"]').val()
    var txt = $parent.find('input[name="details"]').val()
    var text = $parent.find('textarea[name="text"]').val()
    var edt = $parent.find('input[name="edt"]').val()
    var date = $parent.find('input[name="date"]').val()
    var mmbr = $parent.find('input[name="mmbr"]').val()
    if(txt.replace(/\s+/g, '').length && date.length){
        Dajaxice.imiagroup.new_task(new_task_callback, {'id': id, 'mmbr': mmbr, 'txt': txt, 'text': text, 'date': date, 'stage': stage, 'edt': edt})
    }
});

$(document).delegate('.accept_tasks_btn', 'click', function(){
    var arr = []
    $('input[name="accept_task"]:checked').each(function(){
        arr.push($(this).val())
        $(this).parents('tr').css({'background': '#C7E0C7'})
    })
    if(arr.length){
        Dajaxice.imiagroup.accept_tasks(false, {'arr': arr})
    }
});


function new_task_callback(data){
    if(data.status){
        if(data.edt > 0){
            $('#tr_' + data.edt).find('.task_txt_edit').text(data.txt)
            $('#tr_' + data.edt).find('#tsk_date').text(data.date)
            $('#tr_' + data.edt).find('#tsk_text').text(data.text)
        }else{
            $('#future_tasks_tbl').append(data.html).show()
        }
        $('.new_task_form').find('input[name="details"]').val('')
        $('.new_task_form').find('input[name="date"]').val('')
        $('.new_task_form').hide()
        $('#future_tasks').show()
    }else{
        alert(data.html)
    }
}

function budget_open_callback(data){
    if(data.status){
        $.fancybox(data.content)
    }
}

$(document).delegate('.tasks_link', 'click', function(){
    var id = $(this).attr('id').replace('t_','')
    $("#" + id + '_tasks').toggle()
    $('.new_task_form').hide()
    $.fancybox.update()
});

$(document).delegate('#jmember', 'change', function(){
    var id = $(this).children(":selected").val()
    var project = $(this).attr('proj')
    Dajaxice.imiagroup.budget_open(budget_open_callback, {'id': project, 'member': id})
});

function post_edit(edit){
    $('.article').hide()
    $('.post_block').show()
    $('input[name="edit"]').val(edit)
    if(edit == 0){
        $('input[name="news_title"]').val('')
        tinyMCE.getInstanceById('id_text').setContent('')
        $('input[name="visible"]').prop('checked', true)
    }else{
        $('input[name="news_title"]').val($('#title_hidden').val())
        tinyMCE.getInstanceById('id_text').setContent($('#text_hidden').text())
        $('input[name="visible"]').prop('checked', $('#visible_hidden').prop('checked'))
    }
}

function booking_fullscreen(){
    $el = $('.content-main')
    if($el.hasClass('onfullscreen')){
        $el.removeClass('onfullscreen')
        $el.css({'height': '70%'})
        $('#show_modal, .footer, .mobile_version, .upper-menu').show()
        $(window).resize()
        $.cookie("onfullscreen", null, { path: '/' })
    }else{
        $el.addClass('onfullscreen')
        height = $(window).height()
        $('.onfullscreen').css({'height': height + 'px'})
        $('#show_modal, .footer, .mobile_version, .upper-menu').hide()
        $('.art-posttree-width, .art-postcontent-width').css('height', height + 'px')
        $.cookie("onfullscreen", window.location.href, { expires: 7, path: "/" })
    }
}

function fullscreen(el){
    if($(el).hasClass('fullscreen')){
        $(el).removeClass('fullscreen')
        $.cookie("fullscreen", null, { path: '/' })
    }else{
        $(el).addClass('fullscreen')
        var url = window.location.href
        $.cookie("fullscreen", url, { expires: 7, path: "/" })
    }
}


function org_edit_submenu_callback(data){
    $('.organization_menu_fields').hide()
    $('#accordion').show()
    if(data.status){
        li = ''
        var idd = data.id + '_section' + data.menu_id
        if(data.menu_id == 'about'){
            li = '<li><a href="/" id="">About Us</a></li>'
            var idd = data.menu_id + '_section'
        }
        for(i in data.arr){
            li += '<li><a href="' + data.arr[i].link + '" id="link_menu__' + data.menu_id + '">' + data.arr[i].val + '</a></li>'
        }
        var id = data.id + '_section' + data.menu_id
        $('.' + id).html(li)
        $('#accordion').accordion('destroy').accordion({ active: $('#' + idd) })
    }
}

function org_add_menu_callback(data){
    $('.org_addmenu_bl_fields').hide()
    if(data.status){
        
        var id = data.id + '_section' + data.menu_id
        if(data.new_menu == 1){
            
            var menu = '<h5 class="method-category" id="' + id + '"><p>' + data.title + '</p><a href="#" class="org_menu_title_edit">edit</a></h5><div class="method-list"><ul class="' + id + '"><li><a href="' + data.link + '" id="link_menu__' + data.menu_id + '">example link</a></li></ul><a class="org_edit_menu" id="' + data.id + '__' + data.menu_id + '"><b>edit page links</b></a></div>'
            $('#about_section').before(menu)
            $('#accordion').accordion('destroy').accordion({ active: $('#' + id) })
        }else{
            if(data.new_menu == 0){
                $('#' + id).next(".method-list").remove()
                $('#' + id).remove()
            }else{
                $('#' + id).find('p').text(data.title)
            }
        }
    }
}

function org_addmenu_bl(){
    $('.org_addmenu_private').prop('checked', true)
    $('.org_addmenu').attr('id', '')
    $('.org_addmenu_title').val('')
    $('.left_banner').hide()
    $('.org_addmenu_bl_fields').show()
}


function add_question_callback(data){
    if(data.status){
        $('.question_list').prepend(data.content)
        $.fancybox.close()
    }
}

function add_answer_callback(data){
    if(data.status){
        $('#q-tr-no').hide()
        $('.answer_list').append(data.content)
        $.fancybox.close()
    }
}


$(document).delegate('.add_question', 'click', function(){
    var subject = $('.question_subject').val()
    var text = $('.question_txt').val()
    var tags = []
    $('.tagsinput .tg').each(function(){
        tags.push($(this).text())
    });
    if(subject.replace(/\s+/g, '').length > 1){
        $('.question_subject').css({'border': '1px solid #BCBCBC'})
        if(text.replace(/\s+/g, '').length > 1){
            $('.question_txt').css({'border': '1px solid #BCBCBC'})
            Dajaxice.imiagroup.add_question(add_question_callback, {'subject': subject, 'text': text, 'tags': tags})
        }else{
            $('.question_txt').css({'border': '1px solid red'})
        }
    }else{
        $('.question_subject').css({'border': '1px solid red'})
    }
});

$(document).delegate('.add_answer', 'click', function(){
    var text = $('.answer_txt').val()
    if(text.replace(/\s+/g, '').length > 2){
        $('.answer_txt').css({'border': '1px solid #BCBCBC'})
        Dajaxice.imiagroup.add_answer(add_answer_callback, {'text': text})
    }else{
        $('.answer_txt').css({'border': '1px solid red'})
    }

});

$(document).delegate('.org_menu_accept_btn', 'click', function(){
    var org_id = $('input[name="organization_id"]').val()
    var menu_id = $('input[name="menu_id"]').val()

    var arr = []
    var warning = false
    
    $('#org_menu_inputs').find('.organization_menu_field').each(function(){
        if(!$(this).prop('disabled') && $(this).attr('id').length){
            if($(this).val().length == 0){ warning = true }
            arr.push({'id': $(this).attr('id'), 'val': $(this).val()})
        }
    });
    
    if(arr.length > 0){
        if(warning){
            if(confirm("All Articles Related To This Menu Item Will Be Removed. Continue?")) {
                Dajaxice.organizations.org_edit_submenu(org_edit_submenu_callback, {'id': org_id, 'arr': arr, 'menu_id': menu_id})
            }else{
                $('.organization_menu_fields').hide()
                $('#accordion').show()
            }
        }else{
            Dajaxice.organizations.org_edit_submenu(org_edit_submenu_callback, {'id': org_id, 'arr': arr, 'menu_id': menu_id})
        }
    }else{
        alert("The only link can't be deleted!")
        $('.organization_menu_fields').hide()
        $('#accordion').show()
    }
});
    


$(document).delegate('.org_menu_title_edit', 'click', function(){
    $('.left_banner').hide()
    $title = $(this).parents('.method-category')
    var title_txt = $title.find('p').text()
    var private = $(this).attr('private')
    private = typeof private !== 'undefined' ? private : '0'
    var menu_id = $title.attr('id').split('_section')
    org_addmenu_bl()
    $('#accordion').accordion({ active: $('.method-category').last() })
    $('.org_addmenu').attr('id', menu_id[1])
    $('.org_addmenu_title').val(title_txt)
    if(private == '0'){
        $('.org_addmenu_private').prop('checked', false)
    }else{
        $('.org_addmenu_private').prop('checked', true)
    }
});

$(document).delegate('.org_edit_menu', 'click', function(){
    var menu_id = $(this).attr('id').split('__')
    
    if(menu_id[1] == 'about'){
        var title = $('#' + menu_id[1] + '_section').find('p').text()
    }else{
        var title = $('#' + menu_id[0] + '_section' + menu_id[1]).find('p').text()
    }
    
    $menu_ul = $('.' + menu_id[0] + '_section' + menu_id[1])
    $('.organization_menu_fields').find('b').text(title)
    
    $('#org_menu_inputs').html('')
    $menu_ul.find('a').each(function(){
        disabled = ''
        if(!$(this).attr('id').length){
            disabled = ' disabled="disabled"'
        }
        var id = $(this).attr('href')
        var name = $(this).text()
        var input = '<input type="text" value="' + name + '" size="30" class="organization_menu_field" id="' + id + '" ' + disabled +'/>'
        $('#org_menu_inputs').append(input)
        
    });
    
    $('input[name="organization_id"]').val(menu_id[0])
    $('input[name="menu_id"]').val(menu_id[1])
    $("#accordion").hide();
    $(".organization_menu_fields").show();
});


$(document).delegate(".submenu_new", 'click', function(){
    if($('#org_menu_inputs').find('.organization_menu_field').length < 10){
        $('#org_menu_inputs').append('<br />' + '<input type="text" value="" size="24" class="organization_menu_field" id="0" />')
    }else{
        $(this).remove()
    }
});
/* end Post */

/* Music start */
$(document).ready(function(){

    $('.play_audio').click(function(){
        var id = $(this).attr('id').replace('pl_','')
        Dajaxice.music.get_track(get_track_callback, {'id': id})
    });
    
    $('.chkr').click(function(){
        if($(this).is(':checked')){
            $(this).parents('tr').addClass('chkr_bg')
        }else{
            $(this).parents('tr').removeClass('chkr_bg')
        }
    });
    
});

function get_track_callback(data){
    var flash_ver = swfobject.getFlashPlayerVersion();
    
    var flash_err = true
    if(data.flash.major <= flash_ver.major){
        if(data.flash.minor <= flash_ver.minor){
            if(data.flash.release <= flash_ver.release){ flash_err = false }
        }
    }
    
    if(flash_err){
        $('#uppod_player').html("<b>Вам необходимо обновить <a href=\"https://get.adobe.com/flashplayer/\" target=\"_blank\">Adobe Flash Player</a></b>");
    }else{
        var flashvars = {'m':'audio', 'uid': 'uppod_player', 'file': data.path, 'auto': 'play', 'st': data.style}; 
        var params = {bgcolor:"#ffffff", wmode:"window", allowFullScreen:"true", allowScriptAccess:"always"}; 
        var flash = data.flash.major + "." + data.flash.minor + "." + data.flash.release
        swfobject.embedSWF(data.swf, "uppod_player", data.width, data.height, flash, false, flashvars, params);
    }
}

    $(document).delegate('#tagsinput input', 'focusout', function(){    
        var txt = this.value.replace(/[^а-яА-Яa-zA-Z0-9]\+\-\.\#\ /g,'');
        if(txt.replace(/ /g,'')){
            $(this).before('<span class="tg" title="Удалить тег">' + txt.toLowerCase() + '</span>');
        }
        this.value="";
    });
    
    $(document).delegate('#tagsinput input', 'keyup', function(e){
        if(/(13)/.test(e.which)){ $(this).focusout() }    
    });

    $(document).delegate('#tagsinput .tg', 'click', function(){
        $(this).remove()
    });



/* end Music */

/* organizations start */
function organization_staff_callback(data){
    if(data.status == true){
        var staff = ''

        if(data.content.length){
            if(data.extra){
                for(i in data.content){
                    var sep = ''
                    if(data.content[i].city){
                        sep = ' &#8226; '
                    }
                    staff += '<div id="' + data.content[i].id + '" class="recipient_obj">' + data.content[i].acc + sep + '<b>' + data.content[i].city + '</b></div>';
                }
            }else{
                for(i in data.content){
                    staff += '<input type="checkbox" id="checker_' + data.pid + '" value="' + data.content[i].id + '" '+ data.content[i].checked +'/> <a href="http://ya.vsetiinter.net/user/profile/' + data.content[i].id + '/" target="_blank">' + data.content[i].acc + ' &#8226; <b>' + data.content[i].city + '</b></a> <br />';
                }
            }
        }else{
            staff = 'Пусто'
        }

        $('#' + data.pid + '_app').show();
        $('.' + data.pid + '_result').html(staff).show();
    }
}

function organization_invite_callback(data){

    if(data.status == true){
        var msg = ''

        if(data.content == true){
            msg = 'Отправлено'
        }else{
            msg = 'Попробуйте позже'
        }
        $('.org_invite_msg').html(msg).show().fadeOut(3000);
        $("#org_invite").prop('disabled', false);
    }
}


$(document).ready(function(){
    $('.blog_cmmnt').click(function(){
        var pst = $('input[name="pst_id"]').val()
        var answ = $('input[name="answer"]').val()
        var rev = $('input[name="review"]').val()
        var text = $('#id_note1').val()
        var stype = $('input[name="author_nick"]:checked').val()
        if(pst && text.replace(/\s+/g, '')){
            Dajaxice.letsgetrhythm.blog_cmmnt(blog_cmmnt_callback, {'pst': pst, 'answ': answ, 'stype': stype, 'text': text, 'rev': rev});
        }
    });

    $('.lets_mb_readnext').click(function(){
        $(this).prev().toggle();
        $(this).parent().find('#lets_mb_shortcut').toggle();
        $(this).text(function(i, text){
            return text === "[read next]" ? "[shortcut]" : "[read next]"
        });
    });

    $('.search_appoint').click(function(){
        var arr = [];
        var id = $('.organization_id').attr('id');
        var pid = $(this).attr('id').replace('_app','');
        $("input[id='checker_" + pid + "']").each(function(){
            arr.push($(this).val() + ';' + $(this).is(':checked'));
        });
        Dajaxice.organizations.get_organization_staff_appoint(function(){}, {'id': id, 'pid': pid, 'arr': arr});
        $.fancybox.close();
    });

    $("#org_invite").click(function(){
        var id = $('.organization_id').attr('id');
        var email = $('#org_email').text();
        $(this).prop('disabled', true);
        $('.org_invite_msg').html('Подождите...').show();
        Dajaxice.organizations.get_organization_invite(organization_invite_callback, {'id': id, 'email': email});
    });

    $(".organization_site_edit").click(function(){
        $(".organization_site").hide();
        $('.organization_site_fields').show();
    });
    $(".organization_site_cancel_btn").click(function(){
        $(".organization_site_fields").hide();
        $('.organization_site').show();
    });

    $(".organization_note").click(function(){
        $(".organization_note").hide();
        $('.organization_txt').show();
    });
    $(".organization_txt_cancel_btn").click(function(){
        $(".organization_txt").hide();
        $('.organization_note').show();
    });

    $('.organization_braning_edit').click(function(){
        $('.organization_braning_fields').show();
    });
    $('.organization_braning_cancel_btn').click(function(){
        $('.organization_braning_fields').hide();
    });

    $('.news_text_edit').click(function(){
        $(".news_text").hide();
        $('.news_text_editor').show();
    });
    $('.news_text_editor_cancel').click(function(){
        $(".news_text").show();
        $('.news_text_editor').hide();
    });

    $('.organization_people').click(function(){
        var id = $(this).attr('id')
        $.fancybox.open($(".organization_" + id + "_fields").show());
    });

    $("#org_trailers").hover(
        function(){
            $('.organization_trailer_edit').show();
        },
        function(){
            $('.organization_trailer_edit').hide();
        }
    );

    $(".organization_trailer_edit").click(function(){
        $(".trailer").hide();
        $("#org_trailers").append($('.organization_trailer').show());
    });
    $(".organization_trailer_cancel_btn").click(function(){
        $(".trailer").show();
        $('.organization_trailer').hide();
    });


    $("#org_poster").hover(
        function(){
            $('.organization_poster_edit').show();
        },
        function(){
            $('.organization_poster_edit').hide();
        }
    );

    $(".organization_poster_edit").click(function(){
        $("#poster").hide();
        $("#org_poster").append($('.organization_poster').show());
    });
        $(".organization_poster_cancel_btn").click(function(){
        $("#poster").show();
        $('.organization_poster').hide();
    });


    $("#org_slides").hover(
        function(){
            $('.organization_slides_edit').show();
        },
        function(){
            $('.organization_slides_edit').hide();
        }
    );

    $(".organization_slides_edit").click(function(){
        $(".organization_slides").show();
    });
        $(".organization_slides_cancel_btn").click(function(){
        $('.organization_slides').hide();
    });

    $("#org_slides .slide").hover(
        function(){
            $(this).find('span').show();
        },
        function(){
             $(this).find('span').hide();
        }
    );

    $('.organization_slides_d').click(function(){
        if (confirm("Вы уверены, что хотите удалить слайд?")) {
            var id = $('.organization_id').attr('id');
            var slide = $(this).attr('id');
            Dajaxice.organizations.get_organization_slides(function(){}, {'id': id, 'slide': slide});
            $(this).parent().html('Нет слайда');
        }
    });

    $(".organization_url").fancybox({
         'padding': 0,
         'autoScale': false,
         'width': '90%',
         'height': '90%',
         'type': 'iframe'
    });

    $(".org_new").click(function(){
        $.fancybox.open($(".organization_new").show());
    });

    $(".org_name_tag_new").click(function(){
        if($('.organization_name_tag').length < 6){
            $(this).before('<input type="text" value="" size="20" class="organization_name_tag" onkeyup="get_names_auto(this, \'tags\');" />');
        }else{
            $('.org_name_tag_new').remove();
        }
    });


    $(".phone_new").click(function(){
        if($('.organization_phones_field').length < 10){
            var full = window.location.host.split('.')
            var sub = full[0]
            var pre = ''
            $(this).before('<br />' + pre + '<input type="text" value="" size="20" class="organization_phones_field" />');
        }else{
            $('.phone_new').remove();
        }
    });

    $(".org_del").click(function(){
        if (confirm("Вы уверены, что хотите удалить организацию?")) {
            $('.organization_del').submit();
        }
    });

    $(".organization_new_btn").click(function(){
        var name = $('.organization_n').val().replace(/\s+/g, '')
        var tag = $('.organization_t').val().replace(/\s+/g, '')
        if(name.match(/[a-zа-яА-ЯA-Z]/g) && tag.match(/[a-zа-яА-ЯA-Z]/g)){
            $(this).parent().submit()
        }else{
            $(this).parent().find('b').animate({"color": "red"}, 400).animate({"color": "#333"}, 400)
        }
    });

    $(".organization_relations_edit").click(function(){
        $(".organization_relations_fields").show();
        $('.organization_relations').hide();
    });

    $(".relation_new").click(function(){
        if($('.organization_relations_field').length < 10){
            $(this).before('<br /><span class="organization_relations_field">Название: <input type="text" value="" size="25" class="rel_name" /> Ссылка: <input type="text" value="http://" size="40" class="rel_link" /></span>');
        }else{
            $('.relation_new').remove();
        }
    });


    $(".org_add_menu").click(function(){
        $("#accordion").hide();
        $(".organization_menu1_fields").show();
    });
    $('.organization_menu1_cancel_btn').click(function(){
        $("#accordion").show();
        $(".organization_menu1_fields").hide();
    });
    $('.organization_menu_cancel_btn').click(function(){
        $("#accordion").show();
        $(".organization_menu_fields").hide();
    });

    $(".org_add_menu_needs").click(function(){
        $("#accordion").hide()
        $(".organization_menu_needs_fields").show()
    });
    $('.organization_menu_needs_cancel_btn').click(function(){
        $("#accordion").show()
        $(".organization_menu_needs_fields").hide()
    });

    $(".organization_name_edit").click(function(){
        $(".organization_name").hide()
        $(".organization_name_fields").show()
    });

    $('.organization_menu_accept_btn').click(function(){
        var arr = []
        $(this).parent().hide()
        $(this).parent().find('.organization_menu_field').each(function(){
            val = $(this).val()
            oid = $(this).attr('id')
            val = val + '~%~' + oid
            $(this).val(val)
        });
        $(this).parent().parent().submit()
    });


    $('.leave_comment_btn').click(function(){
        $('.leave_comment').toggle()
        $('.leave_comment_btn').text(function(i, text){
            return text === "Добавить новый" ? "Скрыть форму" : "Добавить новый"
        });
    });
    
    
    
    $('.organization_org_ka_accept_btn').click(function(){
        var movie = $('.organization_org_ka_selector').val()
        var id = $('.organization_id').attr('id')
        Dajaxice.organizations.set_organization_org_ka(organization_org_ka_callback, {'id': id, 'movie': movie});
    });
    
    $('.org_sch').on('change', function(){
        var id = $(this).children(":selected").val()
        $('.org_sch_dt').hide()
        $('#org_sch_dt_' + id).show()
    });
    
});

function blog_cmmnt_callback(data){
    if(data.status){
        if(data.msg.length){
            $('.blog_cmmnt_warning').html(data.msg)
        }else{
            location.reload()
        }
    }
}

function organization_org_ka_callback(data){
    if(data.status){
        $('.org_ka_link').html('').html(data.content)
        $('.organization_org_ka_fields').hide()
        $('.organization_org_ka').show()
    }
}

function get_organization_relations_callback(data){
    if(data.status == true){
        var rel = ''
        for(i in data.content){
            rel += '<a href="' + data.content[i].link + '" target="_blank">' + data.content[i].name + '</a><br />'
        }
        if(!rel){
            rel = 'Нет'
        }
        $('.organization_relations').html(rel)
        $(".organization_relations_fields").hide()
        $('.organization_relations').show()
    }
}


$(document).delegate(".menu_new", 'click', function(){
    if($(this).parent().find('.organization_menu_field').length < 10){
        $(this).before('<br />' + '<input type="text" value="" size="30" name="organization_menu_field" class="organization_menu_field" id="0" />')
    }else{
        $('.menu_new').remove()
    }
});

$(document).delegate('.search_people_btn', 'click', function(){
    var id = $('.organization_id').attr('id')
    id = typeof id !== 'undefined' ? id : null
    var pid = $(this).attr('id')
    var val = $(".search_" + pid).val()
    if(val){
        Dajaxice.organizations.get_organization_staff(organization_staff_callback, {'val': val, 'id': id, 'pid': pid})
    }
});


$(document).delegate('.organization_relations_accept_btn', 'click', function(){
    var id = $('.organization_id').attr('id')
    var arr = []
    $('.organization_relations_field').each(function(){
        var name = $(this).children( ".rel_name" ).val()
        var link = $(this).children( ".rel_link" ).val()
        if(name){
            var val = name + '~%~' + link
            arr.push(val);
        }
    });
    Dajaxice.organizations.get_organization_relations(get_organization_relations_callback, {'id': id, 'arr': arr})
});


$(document).delegate('.organization_address_accept_btn', 'click', function(){
    var id = $('.organization_id').attr('id')
    var type = $(".organization_street_types").val()
    var name = $(".organization_street_name").val()
    var area = $(".organization_street_area").val()
    var build = $(".organization_street_number").val()
    var tag = $(".organization_guide").val()
    var city = $(".city_in_card").val()
    area = typeof area !== 'undefined' ? area : ''
    city = typeof city !== 'undefined' ? city : ''
    Dajaxice.organizations.get_organization_address(get_organization_address_callback, {'id': id, 'type': type, 'name': name, 'building': build, 'tag': tag, 'area': area, 'city': city})
});


$(document).delegate('.organization_phones_accept_btn', 'click', function(){
    var id = $('.organization_id').attr('id')
    var arr = []
    $('.organization_phones_field').each(function(){
        val = $(this).val()
        if(val){
            arr.push(val)
        }
    });
    Dajaxice.organizations.get_organization_phones(get_organization_phones_callback, {'id': id, 'arr': arr})
});


$(document).delegate('.organization_site_accept_btn', 'click', function(){
    var id = $('.organization_id').attr('id')
    var val = $(".organization_site_field").attr('value')
    Dajaxice.organizations.get_organization_site(get_organization_site_callback, {'id': id, 'val': val})
});

$(document).delegate('.organization_email_accept_btn', 'click', function(){
    var id = $('.organization_id').attr('id')
    var val = $(".organization_email_field").attr('value')
    Dajaxice.organizations.get_organization_email(get_organization_email_callback, {'id': id, 'val': val})
});

$(document).delegate('.organization_name_accept_btn', 'click', function(){
    var id = $('.organization_id').attr('id')
    var val = $(".organization_name_field").val()
    var own = $(".organization_ownership").val()
    own = typeof own !== 'undefined' ? own : ''
    Dajaxice.organizations.get_organization_name(get_organization_name_callback, {'id': id, 'val': val, 'own': own})
});

$(document).delegate('.organization_name_tag_accept_btn', 'click', function(){
    var type = $(this).attr('id')
    var id = $('.organization_id').attr('id')
    var arr = []
    $('.organization_name_tag').each(function(){
        val = $(this).val()
        if(val){
            arr.push(val)
        }
    });
    if(!arr.length){
        $('.tags_err').html('Обязательное поле')
    }else{
        Dajaxice.organizations.get_organization_tags(get_organization_tags_callback, {'id': id, 'arr': arr, 'type': type})
    }
});

function get_organization_address_callback(data){
    if(data.status == true){
        $('.organization_address_fields').hide()
        $(".organization_address").html(data.content).show()
        if(data.tag){
            $(".guide").html('(' + data.tag + ')')
        }else{
            $(".guide").html('')
        }
    }
}

function get_organization_tags_callback(data){
    if(data.status == true){
        var tags = ''
        for(i in data.content){
            tags += data.content[i] + '; '
        }
        if(data.type == '1'){
            $('.organization_name_fields').hide()
            $('.organization_name').show()
        }
    }
}

function get_organization_phones_callback(data){
    if(data.status == true){
        var phones = ''
        var pre = $('.phone_new').attr('id')
        for(i in data.content){
            phones += pre + data.content[i] + '; '
        }
        if(!phones){
            phones = 'Нет'
        }
        $('.organization_phones_fields').hide()
        $('.organization_phones').html(phones).show()
    }
}

function get_organization_site_callback(data){
    if(data.status == true){
        $('.organization_site_fields').hide();
        $('.organization_site').show();
        if(!data.content){
            $('.organization_site').html('Нет');
        }else{
            $('.organization_site').html('<a href="' + data.content + '" class="organization_url">' + data.content + '</a>')
        }
    }
}

function get_organization_email_callback(data){
    if(data.status == true){
        if(data.err != true){
            $('.organization_email_fields').hide();
            $('.organization_email').html(data.content).show();
        }else{
            $('.email_err').html('Укажите E-mail');
        }
    }
}

function get_organization_name_callback(data){
    if(data.status == true){
        if(data.err != true){
            $('.organization_name_fields').hide();
            $('.organization_name').html(data.content).show();
        }else{
            $('.name_err').html('Укажите Название');
        }
    }
}

/* organizations end */



/* begin feedback_in_modal */
$(document).ready(function(){
    $('#modal').fancybox();
    $('#modal').click(function(){
        Dajaxice.feedback.feedback_user_request(call_madal_callback, {});
    });
});

// обработка клика по кнопке тип1
$(document).delegate('#modal_send1', 'click', function(){
    var resend = true;
    var msg = $("#msg").val();
    var msglen = msg.length;
    $("#thx").html('').html('');

    if($("#email").val()) {
        resend = true;
        var emailval = $("#email").val();
    }else{
        resend = false;
        var emailval = $("#email").val();
    }

    // если сообщение короче 10
    if(msglen > 1){
        var domain = window.location.host
        if(domain == 'letsgetrhythm.com.au' || window.location.host == 'vladaalfimovdesign.com.au'){
            thanks = 'Thanks!'
        }else{
            thanks = 'Спасибо за сообщение!'
        }
        // получаем урл страницы вызова
        var get_url = document.URL;
        // отсылаем сообщение
        send_user_message(msg, emailval, get_url, resend);
        // завершаем модальное окно
        $("#thx").append('<strong>' + thanks + '</strong>');
        setTimeout("$.fancybox.close()", 1000);
    }
});

// обработка клика по кнопке тип2
$(document).delegate('#modal_send2', 'click', function(){
    var resend = true;
    var msg = $("#msg").val();
    var msglen = msg.length;
    $("#thx").html('').html('');

    // с применением jQuery получаю значение выбранного e-mail
    if($("#selectEmail option:selected").val() != 777){
        var emailval = $("#selectEmail option:selected").val()
        resend = true;
    }else{
        // если e-mail не указан
        var emailval = ""
        resend = false;
    }

    // если длинна сообщения меньше 10
    if(msglen > 1){
        var domain = window.location.host
        if(domain == 'letsgetrhythm.com.au' || window.location.host == 'vladaalfimovdesign.com.au'){
            thanks = 'Thanks!'
        }else{
            thanks = 'Спасибо за сообщение!'
        }
        // получаем урл страницы вызова
        var get_url = document.URL;
        // отсылаем сообщение
        send_user_message(msg, emailval, get_url, resend);
        // завершаем модальное окно
        $("#thx").append('<strong>' + thanks + '</strong>');
        setTimeout("$.fancybox.close()", 1000);
    }

});

function send_user_message(msg, emailval, get_url, resend){
    Dajaxice.feedback.send_user_message(function(){}, {'msg': msg, 'emailval': emailval, 'get_url': get_url, 'resend': resend});
}


function call_madal_callback(data){
    var domain = window.location.host
    if(domain == 'letsgetrhythm.com.au' || window.location.host == 'vladaalfimovdesign.com.au'){
        label1 = 'If you want get answer choose email address'
        label2 = 'Message'
        label3 = 'Send'
    }else{
        label1 = 'Оставьте Ваш e-mail, если хотите получить ответ'
        label2 = 'Оставьте Ваше сообщение'
        label3 = 'Отправить'
    }
    
    var txt = ''

    if(data.is_email == true){
        txt += ' <br />' + label1 + '<br /><br /><select class="modal-select" id="selectEmail" name="selectEmail"><option value="777">--------------------</option> '

        for(var i=0; i<data.emails.length; i++){
            var value = data.emails[i];
            txt += '<option value="' + value + '">' + value + '</option>'
        }

        txt += '</select><br /><br />' + label2 + '<br />' +'<textarea id="msg" name="msg" class="txtarea"/>' +  '<input id="modal_send2" type="button" value="' + label3 + '">' +' <br /><p id="thx"></p><br />'
    }else{
        txt += ' <br />' + label1 + '<br />' + '<input type="text" id="email" name="email" class="txt" value=""/>' + ' <br />' + label2 + '<br />' + '<textarea id="msg" name="msg" class="txtarea"/>' + '<input id="modal_send1" type="button" value="' + label3 + '">' + '<br /><p id="thx"></p><br />'
    }
    $('#in_modal').html('').html(txt);
}

/* end feedback_in_modal */

/* begin tag-meta_redact */
$(document).delegate('.alt_name_tag', 'click', function(){
    $('#input_alt_name').toggle();
    $('#input_alt_name').html('').html('<input type="text" value="" name="org_meta_tag_alter_name" size="10" class="organization_meta_tag_alter_name" id="input_alter_name" /><input type="button" value="добавить" class="btnAdd_meta_tag_alter_name" /> алт. назв.');

});


$(document).delegate('.group_flag', 'change', function(){
    var meta_flag = $(this).val();
    var meta_flag_id = $(this).attr('id');

    $('.organization_tags_field').each(function(){
        var meta_input_val = $(this).attr('value');
        var meta_input_id = $(this).attr('id');

        if(meta_input_id==meta_flag_id){
            alert("Обновленно");
            Dajaxice.organizations.update_org_meta_tags_flag(function(){}, {'meta_input_val':meta_input_val, 'meta_flag':meta_flag});
        }
    });
});

$(document).delegate('.alt_name_tag', 'click', function(){
    var alt_name_btn_id = $(this).attr('id');

    $('.btnAdd_meta_tag_alter_name').click(function(){
        var alter_name = $('#input_alter_name').val();
        $('.organization_tags_field').each(function(){
            var meta_input_val = $(this).attr('value');
            var meta_input_id = $(this).attr('id');
            if(meta_input_id==alt_name_btn_id){
                Dajaxice.organizations.update_org_meta_tags_alter_name(function(){}, {'meta_input_val':meta_input_val, 'alter_name':alter_name});
                alert("Обновленно");
                $('#input_alt_name').toggle();
                }
         });
    });
});

/* end tag-meta_redact */


/* begin messenger */

$(document).ready(function(){

    $('#mes_modal').click(function(){
        if(window.location.host == 'letsgetrhythm.com.au' || window.location.host == 'vladaalfimovdesign.com.au'){load = 'Loading...'}else{load = 'Загрузка...'}
        $('#messanger_nav__new_dialog').prop('disabled', false);
        $('#messanger_nav__exist_dialog').prop('disabled', true);
        $('.message_recipients_fields').hide();
        $('.messanger_textarea_container').html($('.messanger_textarea').hide());
        $('.message_recipients').html('');
        $('.message_create').hide();
        $.fancybox.open($('#show_messenger').show());
        $.fancybox.update()
        $('.messanger_content').html(load);
        Dajaxice.user_registration.get_messenger(get_messenger_callback, {});
    });

    $('#messanger_nav__new_dialog').click(function(){
        $('.messanger_textarea_container').html($('.messanger_textarea').hide());
        $('.message_recipients').html('');
        $('.message_create').hide();
        $('.messanger_content').html($('.message_recipients_fields').show());
        $('#messanger_nav__new_dialog').prop('disabled', true);
        $('#messanger_nav__exist_dialog').prop('disabled', false);
    });

    $('#messanger_nav__exist_dialog').click(function(){
        if(window.location.host == 'letsgetrhythm.com.au' || window.location.host == 'vladaalfimovdesign.com.au'){load = 'Loading...'}else{load = 'Загрузка...'}
        $('#messanger_nav__new_dialog').prop('disabled', false);
        $('#messanger_nav__exist_dialog').prop('disabled', true);
        $('.message_recipients_fields_container').html($('.message_recipients_fields').hide());
        $('.message_recipients').html('');
        $('.message_create').hide();
        $('.messanger_textarea_container').html($('.messanger_textarea').hide());
        $('.messanger_content').html(load);
        $('.messanger_nav').show()
        $.fancybox.update()
        Dajaxice.user_registration.get_messenger(get_messenger_callback, {});
    });

});


function get_messenger_send_callback(data){
    $('.message_send').prop('disabled', false);
    if(window.location.host == 'letsgetrhythm.com.au' || window.location.host == 'vladaalfimovdesign.com.au'){err = 'Error'}else{err = 'Ошибка'}
    if(data.status){
        $('.message_send_warning').html('');
        if(data.type == 0){
            $('.messenger__txt').val('');
            $('#messanger_nav__exist_dialog').click();
        }else{
            $('.messanger_textarea_container').html($('.messanger_textarea').hide());
            $('.message_recipients').html('');
            $('.message_create').hide();
            $('.message_send__dialog').prop('disabled', false);
            get_messenger_dialog_callback(data);
        }
        $('.messanger_nav').show()
    }else{
        $('.message_send_warning').html(err);
    }
}

function get_messenger_callback(data){
    if(data.status){
        if(window.location.host == 'letsgetrhythm.com.au' || window.location.host == 'vladaalfimovdesign.com.au'){
            label1 = 'Delete dialog'
            label2 = 'new'
            label3 = 'No one dialog yet'
        }else{
            label1 = 'Удалить диалог'
            label2 = 'новых'
            label3 = 'У Вас пока нет диалогов'
        }
        var dialogs = ''
        if(data.content.length != 0){
            for(i in data.content){
                var news = ''
                if(data.content[i].news > 0){
                    news = ' new_exist'
                }
                dialogs += '<div class="dialog_short"><div class="cntnt" id="' + data.content[i].id + '"><span>' + data.content[i].users + '</span></div><div class="dialog_del" id="' + data.content[i].id + '" title="' + label1 + '"></div><div class="new_msg_count' + news + '">' + label2 + ': ' + data.content[i].news + '</div></div>'
            }
        }else{
            dialogs = label3
        }
        $('.messanger_content').html(dialogs)
    }
}

$(document).delegate('.message_send', 'click', function(){
    if(window.location.host == 'letsgetrhythm.com.au' || window.location.host == 'vladaalfimovdesign.com.au'){
        label1 = 'Sending...'
        label2 = 'Write message'
    }else{
        label1 = 'Отправляем...'
        label2 = 'Напишите сообщение'
    }
    var one = $('.message_send_one_dialog').prop('checked')
    $('.message_send_warning').html(label1);
    var uids = []
    $('.recipient_block').each(function(){
        var uid = $(this).attr('id');
        uids.push(uid);
    });
    var msg = $('.messenger__txt').val();
    var msg_tmp = msg.replace(/\s+/g, '');
    if(msg_tmp){
        $('.message_send').prop('disabled', true);
        var dialog = $('.message_dialog').val();
        Dajaxice.user_registration.get_messenger_send(get_messenger_send_callback, {'uids': uids, 'msg': msg, 'dialog': dialog, 'one': one});
    }else{
        $('.message_send_warning').html(label2);
    }
});


$(document).delegate('.recipient_block', 'click', function(){
    $(this).remove()
    if($('.message_create').find('.recipient_block').length == 0){
        $('#messanger_nav__exist_dialog').click()
        $('.message_create, #messanger_nav__new_dialog').hide()
    }
});

$(document).delegate('.dialog_del', 'click', function(){
    if (confirm("Вы уверены, что хотите удалить диалог?")) {
        id = $(this).attr('id')
        Dajaxice.user_registration.get_messenger_del(function(){}, {'id': id})
        $(this).parent().remove()
    }
});

$(document).delegate('.cntnt', 'click', function(){
    id = $(this).attr('id')
    if(window.location.host == 'letsgetrhythm.com.au' || window.location.host == 'vladaalfimovdesign.com.au'){load = 'Loading...'}else{load = 'Загрузка...'}
    $('.messanger_content').html(load);
    $('.messenger__txt__dialog').val('');
    Dajaxice.user_registration.get_messenger_dialog(get_messenger_dialog_callback, {'id': id});
});


$(document).delegate('.message_send__dialog', 'click', function(){
    var uids = []
    if(window.location.host == 'letsgetrhythm.com.au' || window.location.host == 'vladaalfimovdesign.com.au'){
        label1 = 'Sending...'
        label2 = 'Write message'
    }else{
        label1 = 'Отправляем...'
        label2 = 'Напишите сообщение'
    }
    $('.message_send_warning').html(label1);
    var msg = $('.messenger__txt__dialog').val();
    var msg_tmp = msg.replace(/\s+/g, '');
    if(msg_tmp){
        $('.message_send__dialog').prop('disabled', true);
        var dialog = $('.message_dialog__dialog').val();
        Dajaxice.user_registration.get_messenger_send(get_messenger_send_callback, {'uids': uids, 'msg': msg, 'dialog': dialog});

    }else{
        $('.message_send_warning').html(label2);
    }
});


function get_messenger_dialog_callback(data){
    if(data.status){
        $('.messenger__txt__dialog').val('')
        var messages = '<div class="messages_container">'
        var system = false
        for(i in data.content){
            var id = ''
            if(data.content[i].last){
                id = ' id="last_msg"'
            }
            if(data.content[i].system){
                system = true
            }
            messages += '<div class="message_block"><div class="message_head"' + id + '><span class="' + data.content[i].recipient + '">' + data.content[i].author + '</span> <em>' + data.content[i].dtime + '</em></div><div class="message_text">' + data.content[i].text + '</div></div>'
        }
        messages += '</div>'

        $('.message_dialog__dialog').val(data.dialog)
        $('.messanger_content').html(messages)
        if(!system){
            $('.messanger_content').append($('.messanger_textarea').show())
        }
        $('#messanger_nav__new_dialog').prop('disabled', false)
        $('#messanger_nav__exist_dialog').prop('disabled', false)

        var top = $("#last_msg").offset().top
        $(".messages_container").scrollTop(top)

        $('.messenger_pre_show').removeClass('new_msg_indicator')
    }
}


$(document).delegate('.recipient_obj', 'click', function(){
    if(window.location.host == 'letsgetrhythm.com.au' || window.location.host == 'vladaalfimovdesign.com.au'){del = 'Delete'}else{del = 'Удалить'}
    var val = $(this).text();
    var id = $(this).attr('id');
    if($('.message_recipients').find('.recipient_block').length < 10){
        $('.message_create').show();
        if($('.message_recipients').find('#' + id).length == 0){
            $('.message_recipients').append('<span class="recipient_block" id="' + id + '" title="' + del + '">' + val + ';</span>');
        }
    }
});

/* end messenger */


/* begin intrface_choice */

$(document).delegate('.main_widget__header__interface_cheker', 'click', function(){

    var id = $(this).attr('id');
    if (id == '1_txt_interface')
    {
        interface_type = 1
        block_type = 1
    }
    if (id == '1_graph_interface')
    {
        interface_type = 0
        block_type = 1
    }
    if (id == '2_txt_interface')
    {
        interface_type = 1
        block_type = 2
    }
    if (id == '2_graph_interface')
    {
        interface_type = 0
        block_type = 2
    }
    if (id == '3_txt_interface')
    {
        interface_type = 1
        block_type = 3
    }
    if (id == '3_graph_interface')
    {
        interface_type = 0
        block_type = 3
    }
    if (id == '4_txt_interface')
    {
        interface_type = 1
        block_type = 4
    }
    if (id == '4_graph_interface')
    {
        interface_type = 0
        block_type = 4
    }

    Dajaxice.slideblok.interface_select(slideblock_callback, {'interface_type':interface_type, 'block_type':block_type});

});
function slideblock_callback(data){
    if (data.status){
       location.reload(); 
    }
}
/* end intrface_choice */



/* share42.com | 29.01.2013 | (c) Dimox */
window.onload=function(){e=document.getElementsByTagName('div');for(var k=0;k<e.length;k++){if(e[k].className.indexOf('share42init')!=-1){if(e[k].getAttribute('data-url')!=-1)u=e[k].getAttribute('data-url');if(e[k].getAttribute('data-title')!=-1)t=e[k].getAttribute('data-title');if(e[k].getAttribute('data-image')!=-1)i=e[k].getAttribute('data-image');if(e[k].getAttribute('data-description')!=-1)d=e[k].getAttribute('data-description');if(e[k].getAttribute('data-path')!=-1)f=e[k].getAttribute('data-path');if(!f){function path(name){var sc=document.getElementsByTagName('script'),sr=new RegExp('^(.*/|)('+name+')([#?]|$)');for(var i=0,scL=sc.length;i<scL;i++){var m=String(sc[i].src).match(sr);if(m){if(m[1].match(/^((https?|file)\:\/{2,}|\w:[\/\\])/))return m[1];if(m[1].indexOf("/")==0)return m[1];b=document.getElementsByTagName('base');if(b[0]&&b[0].href)return b[0].href+m[1];else return document.location.pathname.match(/(.*[\/\\])/)[0]+m[1];}}return null;}f=path('share42.js');}if(!u)u=location.href;if(!t)t=document.title;if(!i)i='';function desc(){var meta=document.getElementsByTagName('meta');for(var m=0;m<meta.length;m++){if(meta[m].name.toLowerCase()=='description'){return meta[m].content;}}return'';}if(!d)d=desc();u=encodeURIComponent(u);t=encodeURIComponent(t);t=t.replace('\'','%27');var s=new Array('"#" onclick="window.open(\'http://www.facebook.com/sharer.php?s=100&p[url]='+u+'&p[title]='+t+'&p[summary]='+d+'&p[images][0]='+i+'\', \'_blank\', \'scrollbars=0, resizable=1, menubar=0, left=200, top=200, width=550, height=440, toolbar=0, status=0\');return false" title="Поделиться в Facebook"','"#" onclick="window.open(\'https://plus.google.com/share?url='+u+'\', \'_blank\', \'scrollbars=0, resizable=1, menubar=0, left=200, top=200, width=550, height=440, toolbar=0, status=0\');return false" title="Поделиться в Google+"','"#" onclick="window.open(\'https://twitter.com/intent/tweet?text='+t+'&url='+u+'\', \'_blank\', \'scrollbars=0, resizable=1, menubar=0, left=200, top=200, width=550, height=440, toolbar=0, status=0\');return false" title="Добавить в Twitter"','"#" onclick="window.open(\'http://vk.com/share.php?url='+u+'&title='+t+'&image='+i+'&description='+d+'\', \'_blank\', \'scrollbars=0, resizable=1, menubar=0, left=200, top=200, width=550, height=440, toolbar=0, status=0\');return false" title="Поделиться В Контакте"','"http://my.ya.ru/posts_add_link.xml?URL='+u+'&title='+t+'" title="Поделиться в Я.ру"');var l='';for(j=0;j<s.length;j++)l+='<a rel="nofollow" style="display:inline-block;vertical-align:bottom;width:16px;height:16px;margin:0 6px 6px 0;padding:0;outline:none;background:url('+f+'icons.png) -'+16*j+'px 0 no-repeat" href='+s[j]+' target="_blank"></a>';e[k].innerHTML='<span id="share42">'+l+'</span>';}};};


/* Search result slider */

$(document).ready(function(){

    var $frame = $('.scroll_list.horizontal');
    var $wrap = $frame.parent();
    // Call Sly on frame
    if($frame.length != 0) {
        $frame.sly({
            horizontal: 1,
            itemNav: 'basic',
            smart: 1,
            activateOn: 'click',
            mouseDragging: 1,
            touchDragging: 1,
            releaseSwing: 1,
            startAt: 0,
            scrollBar: $wrap.find('.scrollbar'),
            scrollBy: 1,
            pagesBar: $wrap.find('.pages'),
            activatePageOn: 'click',
            speed: 300,
            elasticBounds: 0,
            easing: 'easeOutExpo',
            dragHandle: 1,
            dynamicHandle: 1,
            clickBar: 1,

            // Buttons
            forward: $wrap.find('.forward'),
            backward: $wrap.find('.backward'),
            prev: $wrap.find('.prev'),
            next: $wrap.find('.next'),
            prevPage: $wrap.find('.prevPage'),
            nextPage: $wrap.find('.nextPage')
        });
    }
});