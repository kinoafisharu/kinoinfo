/*!
 * jQuery Cookie Plugin v1.3.1
 * https://github.com/carhartl/jquery-cookie
 *
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


function content_height(cl, val){
    var scroll_h = ($(window).height() / 100) * val
    $(val).css('height', scroll_h + 'px')
}


/* forum */
function sm_left(){
    $('.slide_menu').attr('id', 'sm_right')
    $('.left_categories, .left_settings, .left_title').hide()
    $('.art-posttree-width').css({'width': '25px', 'min-width': '22px'})
    $('.art-postcontent-width').css({'width': '100%', 'padding-left': '0'})
    $('.slide_menu').attr('title', 'Развернуть меню')
}
function sm_right(){
    $('.slide_menu').attr('id', 'sm_left')
    $('.left_categories, .left_settings, .left_title').show()
    $('.art-posttree-width').css({'width': '30%', 'min-width': '270px'})
    $('.art-postcontent-width').css({'width': '69%', 'padding-left': '31%'})
    $('.slide_menu').attr('title', 'Свернуть меню')
}

$(document).ready(function(){
    $('.full_website').click(function(e){
        e.preventDefault()
        var domain = 'forums.vsetiinter.net'
        var id = $(this).attr('id').replace('fw_type_','')
        $.cookie("mobile", id, { expires: 7, path: "/", domain: domain})
        window.location.replace($(this).attr('href'))
    });

    $('.top-menu-icon').click(function(){
        $('.art-posttree-width').toggle("slide", {direction:"left"});
    });

    is_mobile = $('.is_mobile').val()
    is_mobile = typeof is_mobile !== 'undefined' ? is_mobile : ''

    if(is_mobile != 'm'){
        wf_lmenu = $.cookie("wf_lmenu")
        if(wf_lmenu != 'sm_left' && wf_lmenu != 'sm_right'){
            wf_lmenu = 'sm_right'
            $.cookie("wf_lmenu", wf_lmenu, {expires: 30, path: "/"});
        }

        if(wf_lmenu == 'sm_left'){
            sm_left()
        }else{
            sm_right()
        }
    }

    $("input[name='checker_all']").click(function(){
        var check = $(this).attr('checked') ? true : false
        $("input[name='checker']").each(function(){
            $(this).prop('checked', check)
        });
    });
    /*
    $(".halfscreen_btn").toggle(
        function(){
            var arr = []
            $('.branch').each(function(){
                var id = $(this).attr('href').replace('#','')
                var obj = $('#' + id)
                $(this).after(obj)
                $('#' + id).show()
                arr.push(id)
            })
            $(this).attr('title', 'Свернуть сообщения')
            Dajaxice.forums.forum_topic_counter(forum_topic_counter_callback, {'id': arr})
        },
        function(){
            $('.branch').each(function(){
                var id = $(this).attr('href').replace('#','')
                $('#' + id).hide()
            })
            $(this).attr('title', 'Раскрыть сообщения')
        }
    )
    */

    $(".halfscreen_btn").toggle(
        function(){
            $('.right-bottom').hide()
            $('.right-top').css({'height':'100%'})
            var arr = []
            $('.branch').each(function(){
                var id = $(this).attr('href').replace('#','')
                var obj = $('#' + id)
                $(obj).find('td').css({'display': 'table-cell'})
                $(this).after(obj)
                arr.push(id)
            })
            $('.fmsg .fmsg_h, .fmsg .fmsg_b b').hide()
            $('.fmsg').css({'display': 'table-row', 'border-bottom': '2px solid #ADADAD'}).show()
            $('.branch').css({'background': '#E9E9E9'}).addClass('xbranch').removeClass('branch')
            $('.branch_current').css({'background': '#FFEB99'})
            
            var scroll_to = $('.branch_current').offset().top - ($(".right-top").offset().top - $(".right-top").scrollTop())
            $(".right-top").scrollTop(scroll_to - 20)
            $(this).attr('title', 'Свернуть сообщения')
            Dajaxice.forums.forum_topic_counter(forum_topic_counter_callback, {'id': arr})
        },
        function(){
            $('.right-bottom').css({'height': '34%'})
            var $current = $('.branch_current')
            var id = $current.attr('href').replace('#','')
            $('.rb-data').html($('.fmsg').css({'display': 'block', 'border-bottom': 'none'}).hide())
            $('.fmsg .fmsg_h, .fmsg .fmsg_b b').show()
            $('.fmsg td').css({'display': 'block'})
            $('.xbranch').addClass('branch').removeClass('xbranch')
            $('.branch').css({'background': 'none'})
            $current.css({'background': '#FFEB99'})
            $('.right-bottom, #' + id).show()
            $('.right-top').css({'height':'65%'})
            var scroll_to = $('.branch_current').offset().top - ($(".right-top").offset().top - $(".right-top").scrollTop())
            $(".right-top").scrollTop(scroll_to - 20)
            $(this).attr('title', 'Раскрыть сообщения')
        }
    )
    

    $('.topic_link').click(function(){
        var id = $(this).attr('id').split('__')
        is_mobile = $('.is_mobile').val()
        is_mobile = typeof is_mobile !== 'undefined' ? is_mobile : ''
        if(is_mobile == 'm'){
            is_mobile += '/'
            $('.art-posttree-width').hide()
        }
        window.history.pushState("", "Женский форум", "/women/" + is_mobile + "topic/" + id[1] + "/")
        $('.branch_title').html($('#item_' + id[0]).find('h3').text())
        $('.branch_data').html('<br />Секундочку...')
        $('.bl_branding_string_edit, .bl_branding_banner_edit').hide()
        $('input[name="next"]').val(id[1])
        $('.topic_id').val(id[1])
        $('.rb-data').html('')
        Dajaxice.forums.get_forum_topic(get_forum_topic_callback, {'id': id[1], 'val': id[1]})
    });
    
    $('.rbe_cancel').click(function(){
        $('.rb-msg').hide()
        $('.rb-data').show()
        $.fancybox.close()
    });
    
    $('.rbe_prev_cancel').click(function(){
        $('.rb-data').show()
        $('.rb-preview, .rb-msg').hide()
        $.fancybox.close()
    });
    
    $('.rbe_edit').click(function(){
        is_mobile = $('.is_mobile').val()
        is_mobile = typeof is_mobile !== 'undefined' ? is_mobile : ''
        if(is_mobile == 'm'){
            $.fancybox($('.rb-msg').show(), {'modal': true, 'openEffect': 'none', 'closeEffect': 'none'})
        }else{
            $.fancybox($('.rb-msg').show(), {'modal': true, 'openEffect': 'none', 'closeEffect': 'none', 'width': '85%', 'height': '65%', 'fitToView': false, 'autoSize': false})
        }
        $('.rb-preview, .rb-data').hide()
    });
    
    $('.rb-msg-emo li').click(function(){
        var sm = $(this).attr('title')
        $('.rbe_text').val($('.rbe_text').val() + sm)
    });

    $('.rbe_anonim').click(function(){
        var nick = $('.unick').val()
        if($(this).attr('checked')){
            $('.rbe_uname').css({'background': '#FFFFFF'}).prop('disabled', false).val('')
        }else{
            $('.rbe_uname').css({'background': '#F0F0F0'}).prop('disabled', true).val(nick)
        }
    });
    
    $('.wf_search').click(function(){
        var q = $('.wf_searching').val()
        if(q.replace(/\s+/g, '').length > 3){
            $('.wf_searching_err').hide()
            $('#wf_search_form').submit();
        }else{
            $('.wf_searching_err').show()
        }
    });

    $('.emo-show').mouseover(function(){
        $('.rb-msg-emo').show()
        $('.rb-msg').css({'padding-bottom': '5px'})
    });
    $('.rb-msg-emo').mouseleave(function(){
        $('.rb-msg-emo').hide()
        $('.rb-msg').css({'padding-bottom': '40px'})
    });

    $('.wf_up').on('change', function(){
        var file = $(this).val()
        if(file.length){
            $('.wf_upload_stat').show()
        }
    });

    $('.wf_upload_cancel').click(function(){
        $('.wf_up').val('')
        $('.wf_upload_stat').hide()
    });

    $('.slide_menu').click(function(){
        var id = $(this).attr('id')
        if(id == 'sm_left'){
            sm_left()
        }else{
            sm_right()
        }
        $.cookie("wf_lmenu", id, {
            expires: 30,
            path: "/",
        });
    });


});

function forum_send_msg_callback(data){
    if(data.status){
        if(data.nerr || data.terr){
            $('.uname_error').html(data.nerr)
            $('.subject_text_error').html(data.terr)
            $('.rbe_send').prop('disabled', false)
        }else{
            var file = $('.wf_up').val()
            
            if(data.mid && file){
                $('.rbe_new_msg_id').val(data.mid)
                $('.rbe_fnext').val(data.next)
                $('#wf_upload_form').submit()
            }else{
                window.location.replace(data.redirect_to)
            }
        }
    }
}

function rbe_send(preview){
    var name = $('.rbe_uname').val()
    var email = $('.rbe_email').val()
    var subject = $('.rbe_subject').val()
    var text = $('.rbe_text').val()
    var anonim = false
    var mtype = $('.msg_type').val()
    var edit = $('.msg_edit').val()
    var edit_id = $('.msg_edit').attr('id').replace('edt__','')
    var topic = $('.topic_id').val()
    var parent = $('.parent_id').val()
    
    if(mtype == 1){
        var parent = $('.category_id').val()
    }
    
    if($('.rbe_anonim').attr('checked')){
        anonim = true
    }
    
    $('.uname_error, .subject_text_error, .file_error, .email_error').html('')
    
    next = true
    if(!name.replace(/\s+/g, '').length){
        $('.uname_error').html('Слишком короткое имя (не менее 1 символа)')
        next = false
    }
    if(!text.replace(/\s+/g, '').length && !subject.replace(/\s+/g, '').length){
        $('.subject_text_error').html('Слишком короткая тема или сообщение')
        next = false
    }
    
    if(email.replace(/\s+/g, '').length){
        if(!IsEmail(email)){
            next = false
            $('.email_error').html('Неверно указан email')
        }
    }
    
    if($('.wf_up').val()){
        var file = $('.wf_up')[0].files[0]
        if(file.size > 5000000){
            next = false
            $('.file_error').html('Слишком большой файл (не более 5 Mb)')
        }else{
            var ext = file.name.split('.').pop()
            exts = ['jpg', 'png', 'jpeg', 'bmp', 'gif']
            if($.inArray(ext.toLowerCase(), exts) === -1){
                next = false
                $('.file_error').html('Неверный тип файла (можно только изображения)')
            }
        }
    }
    
    if(next){
        $('.uname_error, .subject_text_error, .file_error, .email_error').html('')
        //$('.rbe_send').prop('disabled', true)
        $('.rbe_btn').prop('disabled', true)
        data = {'topic': topic, 'parent': parent, 'name': name, 'email': email, 'subject': subject, 'text': text, 'anonim': anonim, 'mtype': mtype, 'preview': preview, 'edit': [edit, edit_id]}
        if(preview){
            var callback = forum_preview_callback
        }else{
            var callback = forum_send_msg_callback
        }
        Dajaxice.forums.forum_send_msg(callback, data)
    }
}


function forum_preview_callback(data){
    $('.rbe_btn').prop('disabled', false)
    if(data.status){
        is_mobile = $('.is_mobile').val()
        is_mobile = typeof is_mobile !== 'undefined' ? is_mobile : ''
    
        if(data.nerr || data.terr){
            $('.uname_error').html(data.nerr)
            $('.subject_text_error').html(data.terr)
            if(is_mobile == 'm'){
                $.fancybox($('.rb-msg').show(), {'modal': true, 'openEffect': 'none', 'closeEffect': 'none'})
            }else{
                $.fancybox($('.rb-msg').show(), {'modal': true, 'openEffect': 'none', 'closeEffect': 'none', 'width': '85%', 'height': '65%', 'fitToView': false, 'autoSize': false})
            }
        }else{
            $('.rb-preview-data').html(data.content)
            if(is_mobile == 'm'){
                $.fancybox($('.rb-preview').show(), {'modal': true, 'openEffect': 'none', 'closeEffect': 'none'})
            }else{
                $.fancybox($('.rb-preview').show(), {'modal': true, 'openEffect': 'none', 'closeEffect': 'none', 'width': '85%', 'height': '65%', 'fitToView': false, 'autoSize': false})
            }
            $('.rb-msg').hide()  
        }
    }
}

function wf_msg(type, id){
    $('.uname_error, .subject_text_error, .file_error, .email_error').html('')
    $('.rbe_email, .rbe_subject, .rbe_text, .wf_up, .rbe_new_msg_id, .rbe_fnext').val('')
    $('.rb-msg').show()
    $('.rb-data').hide()
    $('.msg_edit').val(0).attr('id', 'edt__0')
    var title = ''
    if(type==1){
        $('.category_id').val(id)
        name = $('#item_' + id).text()
        title = name + ': Новая тема'
    }
    if(type==2){
        title = 'Новое сообщение'
    }
    if(type==3){
        $el = $('#' + id)
        var data = $el.find('.fmsg_b').clone()
        
        var bg = $("tr[href^='#" + id + "']").css('background')
        $('.branch_current').removeClass('branch_current').css({'background': bg})
        $("tr[href^='#" + id + "']").addClass('branch_current')

        $(data).find('.wf_img').each(function(){
            $(this).remove()
        })

        title = data.text()
        data.remove()
        
        $('.parent_id').val(id)
    }
    $('.msg_type').val(type)
    $('.rb-msg-title').html(title)

    is_mobile = $('.is_mobile').val()
    is_mobile = typeof is_mobile !== 'undefined' ? is_mobile : ''
    if(is_mobile == 'm'){
        $.fancybox($('.rb-msg').show(), {'modal': true, 'openEffect': 'none', 'closeEffect': 'none', margin: [0, 0, 0, 0]})
    }else{
        $.fancybox($('.rb-msg'), {'modal': true, 'openEffect': 'none', 'closeEffect': 'none', 'width': '85%', 'height': '65%', 'fitToView': false, 'autoSize': false})
    }
}

function get_forum_topic(id, title, val){
    $('.branch_title').html(title)
    $('.branch_data').html('<br />Секундочку...')
    $('.bl_branding_string_edit, .bl_branding_banner_edit').hide()
    Dajaxice.forums.get_forum_topic(get_forum_topic_callback, {'id': id, 'val': val})
}

function get_forum_topic_callback(data){
    if(data.status){
        if(data.error){
            $('.branch_data').html(data.error)
        }else{
            $('.uname_error, .subject_text_error, .file_error, .email_error').html('')
            $('.rbe_email, .rbe_subject, .rbe_text, .wf_up, .rbe_new_msg_id, .rbe_fnext').val('')
            $('.rb-msg').hide()
            
            $('.branch_data').html(data.content)
            $('.rb-data').html(data.msgs).show()
            
            $(".right-top, .right-bottom").scrollTop(0)

            var msg = $('.newmsg').val()
            
            if(msg.length){
                if($('#' + msg).offset()){
                    xtop = $('#' + msg).offset().top - (250 + $('#' + msg).height())
                    $(".right-bottom").scrollTop(xtop)
                    $('.newmsg').val('')
                }
                var mobj = $("tr[href^='#" + msg + "']")
                $(".right-top").scrollTop(mobj.offset().top - 100)
                $(mobj).effect('highlight')
                
                $('#' + msg).css({'display': 'block'}).show()
                
                $(mobj).addClass('branch_current')
            }else{
                var parent = $("tr[href^='#" + data.id + "']")
                var obj = $('#' + data.id).css({'display': 'block'}).show()
                //$(parent).after(obj)
                $(parent).addClass('branch_current')
            }
            
            if(wf_search_query.length){
                $('.branch_data, .fmsg').highlight(wf_search_query)
            }


            is_mobile = $('.is_mobile').val()
            is_mobile = typeof is_mobile !== 'undefined' ? is_mobile : ''
            if(is_mobile == 'm'){

                var arr = []
                $('.branch').each(function(){
                    var id = $(this).attr('href').replace('#','')
                    var obj = $('#' + id)
                    $(obj).find('td').css({'display': 'table-cell'})
                    $(this).after(obj)
                    arr.push(id)
                })
                $('.fmsg .fmsg_h, .fmsg .fmsg_b b').hide()
                $('.fmsg').css({'display': 'table-row', 'border-bottom': '2px solid #ADADAD'}).show()
                $('.branch').css({'background': '#E9E9E9'}).addClass('xbranch').removeClass('branch')
                $('.branch_current').css({'background': '#FFEB99'})
                
                var scroll_to = $('.branch_current').offset().top - ($(".right-bottom").offset().top - $(".right-bottom").scrollTop())
                $(".right-bottom").scrollTop(scroll_to - 20)
                Dajaxice.forums.forum_topic_counter(forum_topic_counter_callback, {'id': arr})
            }
        }
    }
}

function forum_topic_ignore_callback(data){
    if(data.status){
        window.location.replace(data.redirect_to)
    }
}

function get_forum_msg_ignores_callback(data){
    if(data.status){
        $('#' + data.id).find('#igc').css({'padding': '0 12px 12px 12px'}).html(data.content).show()
    }
}

function forum_msglike_callback(data){
    $('.wf_like').prop('disabled', false)
    if(data.status){
        $('#' + data.id).find('.like').val(data.like)
        $('#' + data.id).find('.dislike').val(data.disl)
    }
}

function forum_topic_counter_callback(data){
    if(data.status){
        for(i in data.content){
            $("#" + data.content[i].id).find('.wf_eye i').html(data.content[i].c)
            $("tr[href^='#" + data.content[i].id + "']").find('.tlink').children('div').last().attr('id', data.content[i].n)
        }
        
    }
}

$(document).delegate('.wf_like', 'click', function(){
    var id = $(this).parents('.fmsg').attr('id')
    var type = $(this).attr('id')
    $('.wf_like').prop('disabled', true)
    Dajaxice.forums.forum_msglike(forum_msglike_callback, {'id': id, 'ltype': type})
});

$(document).delegate('#igc', 'mouseleave', function(){
    $(this).hide()
});

$(document).delegate('#igi', 'click', function(){
    var id = $(this).parents('.fmsg').attr('id')
    Dajaxice.forums.get_forum_msg_ignores(get_forum_msg_ignores_callback, {'id': id})
});

$(document).delegate('.wf_edit', 'click', function(){
    $('.uname_error, .subject_text_error, .file_error, .email_error').html('')
    $('.rb-msg-title').html('Редактирование')
    var par = $(this).parents('.fmsg')
    
    var subj = par.find('.fmsg_b b')
    $(subj).find('img').each(function(){
        var attr = $(this).attr('alt')
        $(this).replaceWith(attr)
    })
    subj = subj.html()
    
    var txt = par.find('.fmsg_b span')
    $(txt).find('img').each(function(){
        var attr = $(this).attr('alt')
        $(this).replaceWith(attr)
    })
    txt = txt.html().replace(/\<br>/g, '\n')

    var id = par.attr('id')
    $('.rbe_subject').val(subj)
    $('.rbe_text').val(txt)
    $('.rbe_uname, .rbe_anonim, .rbe_email').prop('disabled', true)
    $('.msg_type').val(2)
    $('.msg_edit').val(1).attr('id', 'edt__' + id)
    $('.rb-data').hide()

    is_mobile = $('.is_mobile').val()
    is_mobile = typeof is_mobile !== 'undefined' ? is_mobile : ''
    if(is_mobile == 'm'){
        $.fancybox($('.rb-msg').show(), {'modal': true, 'openEffect': 'none', 'closeEffect': 'none'})
    }else{
        $.fancybox($('.rb-msg').show(), {'modal': true, 'openEffect': 'none', 'closeEffect': 'none', 'width': '85%', 'height': '65%', 'fitToView': false, 'autoSize': false})
    }
});

$(document).delegate('.wf_ignore', 'click', function(){
    $('.ignore-menu').hide()
    var level = $('.ignore_current_lvl').val()
    var next = $('.ignore_nxt_lvl').val()
    var name = $(this).parents('.fmsg').find('.fmsg_h b').text()
    var menu = '<ul class="ignore-menu"><li id="im-title">Игнорировать "' + name + '":</li>'
    
    menu1 = '<li class="im-val" id="im1">Только это сообщение</li>'
    menu2 = '<li class="im-val-disabled">Все сообщения автора в этой теме (недоступно)</li>'
    menu3 = '<li class="im-val-disabled">Все сообщения автора на форуме (недоступно)</li>'
    
    if(level == 1){
        if(next.length){
            menu2 = '<li class="im-val-disabled">Все сообщения автора в этой теме (будет доступно ' + next + ')</li>'
        }
    }
    if(level == 2){
        menu2 = '<li class="im-val" id="im2">Все сообщения автора в этой теме</li>'
        if(next.length){
            menu3 = '<li class="im-val-disabled">Все сообщения автора на форуме (будет доступно ' + next + ')</li>'
        }
    }
    if(level == 3){
        menu2 = '<li class="im-val" id="im2">Все сообщения автора в этой теме</li>'
        menu3 = '<li class="im-val" id="im3">Все сообщения автора на форуме</li>'
    }
    menu = menu + menu1 + menu2 + menu3 + '</ul>'
    $(this).parent().find('#wfi').html(menu)
});

$(document).delegate('.ignore-menu', 'mouseleave', function(){
    $('.ignore-menu').hide()
});

$(document).delegate('.im-val', 'click', function(){
    var id = $(this).parents('.fmsg').attr('id')
    var val = $(this).attr('id')
    $('.ignore-menu').hide()
    var p = $(this).parents('#wfi').after('<p id="wf_wait">Ожидайте пожалуйста ...</p>')
    Dajaxice.forums.forum_topic_ignore(forum_topic_ignore_callback, {'id': id, 'val': val})
});

$(document).delegate('.xbranch', 'click', function(){
    var id = $(this).attr('href').replace('#','')
    var bg = $(this).css('background')
    $('.branch_current').removeClass('branch_current').css({'background': bg})
    $(this).addClass('branch_current')
});

$(document).delegate('.branch', 'click', function(){
    var id = $(this).attr('href').replace('#','')
    $('.fmsg').hide()
    $('.branch_current').removeClass('branch_current').css({'background': 'none'})
    
    $(this).addClass('branch_current')
    $('#' + id).css({'display': 'block'}).show()
    Dajaxice.forums.forum_topic_counter(forum_topic_counter_callback, {'id': [id]})
    
});

/* endforum */

