/* begin API Panel */
function panel_callback(data){
    if(data.status == 'True'){
        $('#api_panel_status_' + data.value).html('Выполнено')
    }else{
        $('#api_panel_status_' + data.value).html('Ошибка')
    }
}
function api_panel(value){
    var option1 = $('#1_' + value).attr('checked')
    var option2 = $('#2_' + value).attr('checked')
    Dajaxice.base.panel(panel_callback, {'id': value, 'op1': option1, 'op2': option2})
}

function set_merge_list_callback(data){
    $('.merge_list b').html(data.content)
}

function get_merge_list_callback(data){
    var html = ''
    for(i in data.content){
        html += '<span class="del_merge_list" id="dml_' + data.content[i].user_id + '" title="Удалить из списка слияния"></span> <input type="radio" name="ml" value="' + data.content[i].user_id + '" title="Основной" /> <a href="/user/profile/' + data.content[i].user_id + '/" target="_blank">'
        for(j in data.content[i].acc){
            html += data.content[i].acc[j] + ' / '
        }
        html += '</a><br />'
    }
    $('.merge_list b').html(data.count)
    if(html.length){
        html += '<br /><input type="button" value="Сделать слияние" class="merge_list_merger" /> <span id="mlm"></span>'
        $.fancybox(html)
    }else{
        $.fancybox.close()
    }
}

$(document).ready(function(){
    sys_info = $.cookie("sys_info")
    if(sys_info != 'sys_hide' && sys_info != 'sys_show'){
        sys_info = 'sys_show'
        $.cookie("sys_info", sys_info, {expires: 30, path: "/"});
    }
    
    if(sys_info == 'sys_hide'){
        $('.sys_info #slider').removeClass('sys_hide').addClass('sys_show')
        $('.sys_info span').hide()
    }else{
        $('.sys_info #slider').removeClass('sys_show').addClass('sys_hide')
        $('.sys_info span').show()
    }

    $('.sys_info #slider').click(function(){
        var cl = $(this).attr('class')
        if(cl == 'sys_hide'){
            $(this).removeClass(cl).addClass('sys_show')
            $('.sys_info span').hide()
            $.cookie("sys_info", 'sys_hide', {expires: 30, path: "/"});
        }else{
            $(this).removeClass(cl).addClass('sys_hide')
            $('.sys_info span').show()
            $.cookie("sys_info", 'sys_show', {expires: 30, path: "/"});
        }
    });

    $('.add_to_merge_list').click(function(){
        var id = $(this).attr('id').replace('merge__','')
        Dajaxice.base.set_merge_list(set_merge_list_callback, {'id': id})
    });
    
    $('.merge_list').click(function(){
        Dajaxice.base.get_merge_list(get_merge_list_callback, {})
    });

});

$(document).delegate('.del_merge_list', 'click', function(){
    var id = $(this).attr('id').replace('dml_','')
    Dajaxice.base.get_merge_list(get_merge_list_callback, {'id': id})
});

$(document).delegate('.merge_list_merger', 'click', function(){
    var id = $('input:radio[name="ml"]:checked').val()
    if(id){
        $('#mlm').html('Ожидайте...')
        Dajaxice.base.merge_list_merger(function(){ location.reload() }, {'id': id})
    }else{
        alert("Укажите основной аккаунт")
    }
});

/* end API Panel */

/* begin UserRegistration */
$(document).ready(function(){
    $('.gen_auth_link').click(function(){
        var id = $(this).attr('acc_id')
        Dajaxice.user_registration.gen_auth_link(function(data){ $.fancybox('Ссылка для авторизации:<br /><input type="text" size="60" value="' + data.url + '" />') }, {'id': id})
    });
});
/* end UserRegistration */

/* begin Film */
function nof_newcinema_callback(data){
    if(data.status){
        var option = $('<option value="' + data.cinema.kid + '">' + data.cinema.name + ' @ ' + data.cinema.city + '</option>').appendTo('#data_select')
        $('#data_select option[value="' + data.cinema.kid + '"]').attr('selected', 'selected')
        $('#kid_sid').prop('disabled', false).click()
    }
}

function nof_newhall_callback(data){
    if(data.status){
        var option = $('<option value="' + data.hall.id + '">' + data.hall.name + ' @ ' + data.cinema + '</option>').appendTo('#data_select')
        $('#data_select option[value="' + data.hall.id + '"]').attr('selected', 'selected')
        $('#rel').prop('disabled', false).click()
    }
}

$(document).ready(function(){

    $('.nof_newhall').click(function(){
        hall = $('input:radio[class="radio_checker"]:checked').val()
        hall = hall.split(' @ ')
        $('.hall_n').val(hall[0])
        $('.cinemas_names option[id="c' + hall[3] + '"]').attr('selected', 'selected')
        $.fancybox($('.hall_new'))
    });

    $('.nof_newhall_btn').click(function(){
        var name = $('.hall_n').val().replace(/\s+/g, '')
        if(name.match(/[a-zа-яА-ЯA-Z]/g)){
            name = $('.hall_n').val()
            cinema = $('.cinemas_names option:selected').val()
            Dajaxice.organizations.nof_newhall(nof_newhall_callback, {'name': name, 'cinema': cinema})
        }else{
            $(this).parent().find('b').animate({"color": "red"}, 400).animate({"color": "#333"}, 400)
        }
    });



    $('.nof_newcinema').click(function(){
        cinema = $('input:radio[class="radio_checker"]:checked').val()
        cinema = cinema.split(' @ ')
        $('.organization_n').val(cinema[0])
        $('.organization_t').val('Кинотеатр')
        $('.city_in_card_alt option[id="c' + cinema[2] + '"]').attr('selected', 'selected')
        $.fancybox($('.organization_new'))
    });

    $('.nof_newcinema_btn').click(function(){
        var name = $('.organization_n').val().replace(/\s+/g, '')
        var tag = $('.organization_t').val().replace(/\s+/g, '')
        if(name.match(/[a-zа-яА-ЯA-Z]/g) && tag.match(/[a-zа-яА-ЯA-Z]/g)){
            name = $('.organization_n').val()
            tag = $('.organization_t').val()
            city = $('.city_in_card_alt option:selected').val()
            Dajaxice.organizations.nof_newcinema(nof_newcinema_callback, {'name': name, 'tag': tag, 'city': city})
        }else{
            $(this).parent().find('b').animate({"color": "red"}, 400).animate({"color": "#333"}, 400)
        }
    });

    $('.opinion_txt').click(function(){
        var id = $(this).attr('id')
        var txt = $('#txt' + id + ' #txt').text()
        tinyMCE.getInstanceById('id_note').setContent(txt)
        $('.op_id').val(id)
        $('.opinion_txt_fields').show()
    });

    /*
    $('.opinion_rate_set').click(function(){
        var id = $(this).attr('id')
        var alt = $(this).attr('alt')
        var val = $('input:radio[name="rate_' + id + '"]:checked').val()
        var excl = $('#excl').val()
        if(alt == 'set' && val || alt == 'del'){
            Dajaxice.film.opinion_rate_set(opinion_rate_set_callback, {'id': id, 'alt': alt, 'excl': excl, 'val': val})
        }
    });
    */
    $('.opinion_rate_set').click(function(){
        var id = $(this).attr('id')
        var alt = $(this).attr('alt')
        var rate_1 = $('input:radio[name="eye_' + id + '"]:checked').val()
        var rate_2 = $('input:radio[name="mind_' + id + '"]:checked').val()
        var rate_3 = $('input:radio[name="heart_' + id + '"]:checked').val()
        var excl = $('#excl').val()
        if(alt == 'set' || alt == 'del'){
            Dajaxice.film.opinion_rate_set(opinion_rate_set_callback, {'id': id, 'alt': alt, 'excl': excl, 'rate_1': rate_1, 'rate_2': rate_2, 'rate_3': rate_3})
        }
    });


    $('.links_main_page').click(function(){
        Dajaxice.base.links_main_page(links_main_page_callback, {'link1': $('#mlink__1').val(), 'link2': $('#mlink__2').val(), 'link3': $('#mlink__3').val(), 'link4': $('#mlink__4').val()})
    });

    $('.film_create_new_rel').click(function(){
        $('.film_create_new_rel_fields').show()
    });

    $('.rel_name_break').click(function(){
        if(confirm("Вы уверены, что хотите удалить связь?")){
            var kid = $('input[name="kid"]').val()
            var id = $(this).attr('id')
            var type = $(this).attr('href')
            Dajaxice.film.rel_name(rel_name_callback, {'kid': kid, 'id': id, 'ntype': type})
        }
    });

    $('.film_edit_rel_btn').click(function(){
        $('.film_create_rel_fields').show()
        var title = $(this).prev('.organization_url')
        var source_id = $(this).attr('id')
        var source_type = $(this).attr('href').replace('#', '')
        var source = title.prev('b').text()
        $('#get_data_name').val(title.text())
        $('#source_tmp').text(source)
        $('input[name="source_id"]').val(source_id)
        $('input[name="source_type"]').val(source_type)
    });

    $('#sources_select').on('change', function(){
        var source = $(this).children(":selected").val()
        if(source){
            $('#data_rel_select').prop('disabled', true)
            Dajaxice.film.sources_select(sources_select_callback, {'source': source})
        }
    });

    $('.comment_edit').click(function(){
        $('.organization_txt2').show()
        $('.fcomment, #film_trailers, #film_slides').hide()
    });
    
    $('.organization_txt2_cancel_btn').click(function(){
        $('.organization_txt2').hide()
        $('.fcomment, #film_trailers, #film_slides').show()
    });

    $('.edit_persons_name').click(function(){
        var ids = $(this).attr('id').split('__')
        var pid = ids[0]
        var id = ids[1]
        var type = ids[2]
        var name = $(this).text()
        if(name=='ред.'){
            name = ''
        }
        var types = ''
        if(type=='ru'){
            types = 'RUS'
        }else{
            if(type=='en'){
                types = 'ENG'
            }else{
                types = 'RUS род.падеж'
            }
        }
        
        txt = '<b>' + types + '</b>:<br /><input type="text" value="' + name + '" size="40" class="pe_name" id="' + id + '" /><br /><input type="button" value="Сохранить" class="edit_persons_name_btn" /><input type="hidden" value="' + type + '" id="' + pid + '" class="pe_type" />'
        $.fancybox.open(txt)
        $('.pe_name').focus()
    });
    

    $('.limits_edit').click(function(){
        $('.limits_edit_fields').show()
    });
    $('.limits_edit_btn').click(function(){
        $('.limits_edit_fields').hide()
        var limit = $('.limits_val option:selected').val()
        var limit_txt = $('.limits_val option:selected').text()
        var kid = $('input[name="kid"]').val()
        $('.limits_edit').text(limit_txt)
        Dajaxice.film.limits_edit(false, {'kid': kid, 'limit': limit})
    });
    

    $('.imdb_search').click(function(){
        var val = $('#get_data_name').val()
        var exact = $(this).attr('alt')
        
        if(val.length){
            $.fancybox.open('Загрузка...')
            Dajaxice.film.imdb_search(imdb_search_callback, {'val': val, 'exact': exact, 'more': false})
        }
    });
    
    $('.exp_film').click(function(){
        var id = $(this).attr('id')
        $.fancybox.open($(".exp_film_block").show())
        $('.exp_f').hide()
        $(".exp_film_block span").html('Загрузка...')
        Dajaxice.film.get_exp_film(get_exp_film_callback, {'id': id})
    });

    $('.exp_go').click(function(){
        var names = []
        var country = []
        var genre = []
        var distr = []
        var release = []
        var person = []
        var kid = ''
        var pk = ''
        
        if($('.radio_checker').length){
            pk = $('input:radio[class="radio_checker"]:checked').val()
        }
        pk = typeof pk !== 'undefined' ? pk : '';
        
        if($('input[name="kid"]').length){
            kid = $('input[name="kid"]').val()
        }
        
        var imdb = $('input[name="imdb"]').val()
        
        var imdb_rate = ''
        if($('input[name="imdb_rate"]').is(':checked')){
            imdb_rate = $('input[name="imdb_rate"]').val()
        }
        
        var imdb_votes = 0
        if($('input[name="imdb_votes"]').is(':checked')){
            imdb_votes = $('input[name="imdb_votes"]').val()
        }
        
        var year = ''
        if($('input[name="year"]').is(':checked')){
            year = $('input[name="year"]').val()
        }
        
        var runtime = ''
        if($('input[name="runtime"]').is(':checked')){
            runtime = $('input[name="runtime"]').val()
        }
        
        var budget = ''
        if($('input[name="budget"]').is(':checked')){
            budget = $('input[name="budget"]').val()
        }
        
        var limit = ''
        if($('input[name="limit"]').length){
            if($('input[name="limit"]').is(':checked')){
                limit = $('input[name="limit"]').val()
            }
        }else{
            limit = $('select[name="lmts"] option:selected').val()
        }
        
        $('.exp_title').find('input').each(function(){
            if($(this).is(':checked')){
                names.push($(this).val())
            }
        });
        $('.exp_country').find('input').each(function(){
            if($(this).is(':checked')){
                country.push($(this).val())
            }
        });
        if(!country.length){
            country.push($('select[name="cntry"] option:selected').val())
        }
        
        $('.exp_genre').find('input').each(function(){
            if($(this).is(':checked')){
                genre.push($(this).val())
            }
        });
        $('.exp_distr').find('input').each(function(){
            if($(this).is(':checked')){
                distr.push($(this).val())
            }
        });
        /*$('.exp_release').find('input').each(function(){
            if($(this).is(':checked')){
                release.push($(this).val());
            }
        });*/
        $('.exp_person').find('input').each(function(){
            if($(this).is(':checked')){
                person.push($(this).val())
            }
        });
        
        if(country.length <= 2){
            if(genre.length <= 3){
                if(distr.length <= 1){
                    $('.exp_f').hide()
                    $(".exp_film_block span").html('Сохранение...')
                    
                    Dajaxice.film.exp_film(exp_film_callback, {'names': names, 'country': country, 'genre': genre, 'distr': distr, 'release': release, 'person': person, 'imdb': imdb, 'imdb_rate': imdb_rate, 'imdb_votes': imdb_votes, 'runtime': runtime, 'year': year, 'budget': budget, 'limit': limit, 'kid': kid, 'pk': pk})
                }else{
                    alert('Не более 1 дистрибьютора!')
                }
            }else{
                alert('Не более 3 жанров!')
            }
        }else{
            alert('Не более 2 стран!')
        }
        
    });

    $('.new_film_create_btn').click(function(){
        $('.new_film_msg').html('Проверка...')
        var name = $('input[name="new_name"]').val()
        var year = $('input[name="new_year"]').val()
        var lang = $('select[name="new_lang"] option:selected').val()
        if(name.length && year.length){
            Dajaxice.film.name_detect(name_detect_callback, {'name': name})
        }
    });


    $('.film_budget').click(function(){
        $('.film_budget_fields').show()
    });
    $('.film_budget_add_btn').click(function(){
        var kid = $('input[name="kid"]').val()
        var budget = $('input[name="f_budget"]').val()
        if(budget.length){
            $('.film_budget_fields').hide()
            $('.film_budget').attr('title', budget)
            $('.film_budget').css({'color': ''})
            Dajaxice.film.budget_edit(false, {'kid': kid, 'budget': budget})
        }
    });
    

    $('.film_sound').click(function(){
        $('.film_sound_fields').show()
        $('#film_trailers, #film_slides').hide()
    });
    $('.film_sound_add_btn').click(function(){
        var kid = $('input[name="kid"]').val()
        var data = []
        var copies = ''
        var types = ''
        $('.film_sound_fields').find('.sound_item').each(function(){
            var type = $(this).find('select[name="sound_list"] option:selected').val()
            var copy = $(this).find('input[name="film_copy"]').val()
            data.push(type + ';' + copy)
            types += $(this).find('select[name="sound_list"] option:selected').text() + ' '
            copies += copy + ' '
        });
        if(data.length){
            $('.film_sound_fields').hide()
            $('#film_trailers, #film_slides').show()
            $('#film_sound').attr('title', types)
            $('#film_sound').css({'color': ''})
            Dajaxice.film.sound_copy_edit(false, {'kid': kid, 'data': data})
        }
    });
    
    $('.release_add').click(function(){
        $('.film_release_fields').show()
    });
    $('.film_release_add_btn').click(function(){
        var kid = $('input[name="kid"]').val()
        var release = $('input[name="film_release"]').val()
        if(release.length){
            $('.film_release_fields').hide()
            $('.release_add').attr('title', release)
            $('.release_add').css({'color': ''})
        }
        Dajaxice.film.release_edit(false, {'kid': kid, 'release': release})
    });

    $('.release_ua_add').click(function(){
        $('.film_release_ua_fields').show()
    });
    $('.film_release_ua_add_btn').click(function(){
        var kid = $('input[name="kid"]').val()
        var release = $('input[name="film_release_ua"]').val()
        if(release.length){
            $('.film_release_ua_fields').hide()
            $('.release_ua_add').attr('title', release)
            $('.release_ua_add').css({'color': ''})
        }
        Dajaxice.film.release_edit(false, {'kid': kid, 'release': release, 'ru': false})
    });
    

    $('.distr_add').click(function(){
        $('.film_distributor_fields').show()
        $('#film_trailers, #film_slides').hide()
    });

    $('.distr_add_new').click(function(){
        var name = $('.radio_checker:checked').val()
        if(name){
            $('input[name="distributor_name"]').val(name)
            $.fancybox($('.distributor_new').show())
        }
    });



    $('.distributor_add_btn').click(function(){
        $('.film_distributor_fields').hide()
        $('#film_trailers, #film_slides').show()
        var kid = $('input[name="kid"]').val()
        var distr1 = $('select[name="distr_list_1"] option:selected').val()
        var distr2 = $('select[name="distr_list_2"] option:selected').val()
        var distr1_name = $('select[name="distr_list_1"] option:selected').text()
        var distr2_name = $('select[name="distr_list_2"] option:selected').text()
        var txt = ''
        if(distr1 != 0 || distr2 != 0){
            if(distr1 != 0){
                txt += distr1_name
            }
            if(distr2 != 0){
                if(txt.length){
                    txt += ', '
                }
                txt += distr2_name
            }
        }
        if(txt.length){
            $('.distr_add').attr('title', txt)
        }
        Dajaxice.film.distributor_edit(false, {'kid': kid, 'distr1': distr1, 'distr2': distr2});
    });
    
    $(".news_title_cancel_btn").click(function(){
        $(".film_name_en_fields").hide()
        $('.film_name_en').show()
    });

    $(".genre_new").click(function(){
        if($('.film_genres_field').length < 3){
            $(this).before('<br /><input type="text" value="" size="20" class="film_genres_field" onkeyup="get_names_auto(this, \'genres\');" />');
        }else{
            $('.genre_new').remove()
        }
    });
    
    $('.film_sound_new').click(function(){
        if($('.sound_item').length < 5){
            $('.film_sound_fields').find('.sound_item').each(function(){
                var copy = $(this).clone()
                copy.find('input[name="film_copy"]').val('')
                $('.film_sound_new').before(copy)
                return false;
            });
        }else{
            $('.film_sound_new').remove()
        }
    });

    $(".country_new").click(function(){
        if($('.film_countries_field').length < 2){
            $(this).before('<br /><input type="text" value="" size="20" class="film_countries_field" onkeyup="get_names_auto(this, \'countries\');" />')
        }else{
            $('.country_new').remove()
        }
    });

    $("#film_trailers").hover(
        function(){ $(this).find('.film_trailer_edit').show() },
        function(){ $(this).find('.film_trailer_edit').hide() }
    );

    $(".film_trailer_edit").click(function(){
        $(this).parent().find('.trailer').hide()
        $("#film_trailers").append($('.film_trailer').show())
    });
    $(".film_trailer_cancel_btn").click(function(){
        $(".trailer").show()
        $('.film_trailer').hide()
    });

    $(".film_trailer_e").click(function(){
        $('.trailer').show()
        $('.film_trailer').hide()
        $(this).parent().find('.trailer').hide()
        $(this).parent().find('.film_trailer').show()
    });

    $('.film_trailer_accept_btn').click(function(){
        $parent = $(this).parent()
        var val = $parent.find('.film_trailer_code').val()
        if(val.replace(/\s+/g, '')){
            $parent.submit()
        }else{
            if(confirm("Вы хотите удалить трейлер?")){
                $parent.submit()
            }
        }
    });

    $("#film_slides").hover(
        function(){ $('.film_slides_edit').show() },
        function(){ $('.film_slides_edit').hide() }
    );
    
    $('.film_slides_edit').click(function(){
        var kid = $('input[name="kid"]').val()
        Dajaxice.film.slides_poster_edit(false, {'kid': kid, 'status': 1})
    });
    
    $('.film_poster_edit').click(function(){
        var kid = $('input[name="kid"]').val()
        if(kid){
            Dajaxice.film.slides_poster_edit(false, {'kid': kid, 'status': 2})
        }
    });
    
    $("#film_poster").hover(
        function(){ $('.film_poster_edit').show() },
        function(){ $('.film_poster_edit').hide() }
    );

    
    $('.film_left_banner_edit').click(function(){
        $(".film_left_banner_content").hide();
        $('.film_left_banner_fields').show();
    });
    $('.film_left_banner_cancel_btn').click(function(){
        $(".film_left_banner_content").show();
        $('.film_left_banner_fields').hide();
    });


    $('.show_f_details').hover(function(){
        var id = $(this).attr('id');
        $("." + id).show();
    },
    function(){
        var id = $(this).attr('id');
        $("." + id).hide();
    });
    
    $('.create_film_new').click(function(){
        $('.new_film_msg').html('');
        $.fancybox.open($('.film_new_form').show());
    });

});



function imdb_rel_edit(id, name){
    $.fancybox.open('Загрузка...')
    Dajaxice.film.imdb_rel_edit(function(data){$.fancybox(data.content);}, {'name': name})
}

function person_rel_add_callback(data){
    if(data.content.length){
        $('.modern_tbl').append(data.content)
    }
    $.fancybox.close()
    $('.film_person_rel_add_btn').prop('disabled', false)
}


$(document).delegate('.film_person_rel_add_btn', 'click', function(){
    var film = $('.film_id').val()
    var person = $('#data_select').val()
    var type = $('.film_person_rel_add_type').val()
    var status = $('.film_person_rel_add_status').val()
    if(person.length){
        $(this).prop('disabled', true)
        Dajaxice.film.person_rel_add(person_rel_add_callback, {'film': film, 'person': person, 'type': type, 'status': status})
    }
    
});

$(document).delegate('.film_person_rel_del', 'click', function(){
    var $parent = $(this).parents('tr')
    var id = $parent.attr('id').replace('tr_','')
    if(confirm("Вы уверены, что хотите удалить?")){
        Dajaxice.film.person_rel_delete(function(){}, {'id': id})
        $parent.remove()
    }
});

$(document).delegate('.film_person_rel_edit', 'click', function(){
    var $parent = $(this).parents('tr')
    var id = $parent.attr('id').replace('tr_','')
    var type = $parent.find('.film_person_rel_t').attr('id')
    var status = $parent.find('.film_person_rel_s').attr('id')
    $('.film_person_rel_type').val(type)
    $('.film_person_rel_status').val(status)
    $('.film_person_rel_id').val(id)
    $.fancybox($('.film_person_rel_bl').show())
});

$(document).delegate('.film_person_rel_btn', 'click', function(){
    var type = $('.film_person_rel_type').val()
    var type_txt = $('.film_person_rel_type option:selected').text()
    var status = $('.film_person_rel_status').val()
    var status_txt = $('.film_person_rel_status option:selected').text()
    var id = $('.film_person_rel_id').val()
    Dajaxice.film.person_status_edit(function(){}, {'id': id, 'type': type, 'status': status})
    
    $('#tr_' + id + ' .film_person_rel_t').html(type_txt);
    $('#tr_' + id + ' .film_person_rel_s').html(status_txt);
    $.fancybox.close();
});


function opinion_rate_set_callback(data){ 
    var excl = $('#excl').val()
    if(excl == '0' || data.alt == 'del'){
        $('#txt' + data.id).hide().fadeOut(3300).remove()
    }
    $('.art-postheader span').html(data.count)
}

function remove_online_player_callback(data){
    if(data.status){
        $('#player').html('').html(data.player)
    }
}


function links_main_page_callback(data){
    if(data.status){
        $('#links_main_page_msg').html('OK').fadeOut(1500);
    }
}

function rel_name_callback(data){
    if(data.status){
        $('.rel_name__' + data.id).remove();
    }
}

function sources_select_callback(data){
    if(data.status){
        $('#data_rel_select').prop('disabled', false);
        for(i in data.content) {
            var option = $('<option value="' + data.content[i].key + '">' + data.content[i].name + '</option>').appendTo('#data_rel_select');
        }
    }
}

function name_detect_callback(data){
    if(data.status){
        content = ''
        if(data.content.length){
            content = data.content;
            content += '<br /><input type="button" value="Все равно создать" class="force_film_create" />';
            $.fancybox.open(content);
        }else{
            $('.film_new_form_data').submit();
        }
    }
}


$(document).delegate('.background_item_edit', 'click', function(){
    var $parent = $(this).parents('tr')
    var id = $parent.attr('id').replace('lbe_id_','')
    var name = $parent.find('.lbe_title').text()
    var url = $parent.find('.lbe_url').text()
    var date = $parent.find('.lbe_date_bl')
    
    var country = $parent.find('.lbe_country').attr('id')
    var city = $parent.find('.lbe_city').attr('id').split(',')

    $('.background_new_id').val(id)
    $('.background_new_name').val(name)
    $('.background_new_url').val(url)

    $('.lbe_new').show()
    $('.lbe_list').hide()
    
    Dajaxice.base.get_cities_adv(get_cities_adv_callback, {'country': country, 'city': city})
});

$(document).delegate('.adv_tab_constructor', 'click', function(){
    $('.adv_tab_code').removeClass('adv_tab_active')
    $(this).addClass('adv_tab_active')
    $('.lbe_adv_code').hide()
    $('.lbe_adv_new').show()
});
$(document).delegate('.adv_tab_code', 'click', function(){
    $('.adv_tab_constructor').removeClass('adv_tab_active')
    $(this).addClass('adv_tab_active')
    $('.lbe_adv_code').show()
    $('.lbe_adv_new').hide()
});

$(document).delegate('.background_new_cancel', 'click', function(){
    lbe_new_clear()
    $('.lbe_list').show()
    $('.lbe_new').hide()
});

$(document).delegate('.background', 'click', function(){
    var $parent = $(this).parents('tr')
    var id = $parent.attr('id').replace('lbe_id_','')
    var name = $parent.find('.lbe_title').text()
    var url = $parent.find('.lbe_url').text()
    var date = $parent.find('.lbe_date_bl')
    var date_from = date.attr('fr')
    var date_to = date.attr('to')
    var country = $parent.find('.lbe_adv_country').attr('id')
    var city = $parent.find('.lbe_adv_city').attr('id').split(',')
    
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
    
    Dajaxice.base.get_cities_adv(get_cities_adv_callback, {'country': country, 'city': city})
    
});


$(document).delegate('.background_adm_new_btn', 'click', function(){
    lbe_new_clear()
    Dajaxice.base.get_cities_adv(get_cities_adv_callback, {})
});

function background_adm(){
    Dajaxice.base.get_my_blocks(get_my_blocks_callback, {'btype': 2})
}

function adv_adm(){
    Dajaxice.base.get_my_blocks(get_my_blocks_callback, {'btype': 5})
}


function myhit_search(name, year){
    if(name.length){
        $.fancybox.open('Загрузка...');
        Dajaxice.film.myhit_search(imdb_search_callback, {'val': name, 'year': year});
    }
}

function imdb_search(name, year, exact, imdb){
    if(name.length){
        imdb = typeof imdb !== 'undefined' ? imdb : 0;
        var kid = $('.film_id').attr('id')
        if(imdb){
            $.fancybox.open($(".exp_film_block").show());
            $('.exp_f').hide();
            $(".exp_film_block span").html('Загрузка...');
            Dajaxice.film.imdb_search2(get_exp_film_callback, {'imdb_id': imdb, 'name': name, 'year': year, 'kid': kid});
        }else{
            $.fancybox.open('Загрузка...');
            Dajaxice.film.imdb_search(imdb_search_callback, {'val': name, 'exact': exact, 'more': true});
        }
    }
}

function imdb_search_callback(data){
    if(data.status){
        content = 'Поиск по запросу <b>' + data.query + '</b>:<br />' + data.content;
        $.fancybox.open(content)
    }
    else {
        $(".exp_film_block span").html('При загрузке произошла ошибка. Смотрите логи на сервере.');
    }
}

function exp_film_callback(data){
    if(data.status){
        if(data.link){
            var domain = window.location.host;
            window.location.href = "http://" + domain + '/film/' + data.kid + '/';
        }else{
            location.reload(); 
        }
    }
    else {
        $(".exp_film_block span").html('При сохранении данных произошла ошибка. Смотрите логи на сервере.');
    }
}

function get_exp_film_callback(data){
    if(data.status){
        if(data.double){
            var html = '<b>' + data.msg + '</b><br /><br />'
            for(i in data.objs){
                html += '<input type="radio" value="' + data.objs[i].id + '" name="fdoubles" id="' + data.objs[i].imdb + '" />'
                names = ''
                for(j in data.objs[i].names){
                    names += data.objs[i].names[j].name + ', '
                }
                html += ' <a href="/film/' + data.objs[i].kid + '/" target="_blank" >' + names + '</a> '
                html += data.objs[i].year + ' (<a href="http://www.kinoafisha.ru/?status=1&id1=' + data.objs[i].kid + '" target="_blank">связь</a>)<br />'
            }
            html += '<br /><input type="button" value="Выбрать" class="double_select" />'
            $.fancybox.open(html)
        }else{
            if(data.redirect){
                
                var html = '<b>Фильм с таким ID от IMDb уже <a href="/film/' + data.kid +'/" target="_blank">существует</a></b><br /><br />'
                html += '<input type="radio" value="1" name="rb1" /> Удалить текущий фильм и перейти к уже существующему<br />'
                html += '<input type="radio" value="2" name="rb1" /> Удалить уже существующий фильм и оставить текущий<br />'
                html += '<input type="hidden" value="' + data.kid +'" id="exist_imdbfilm" />'
                html += '<br /><input type="button" value="Далее" class="exist_imdbfilm_btn" />'
                $.fancybox(html)
            }else{
        
                var check = ''
                for(i in data.names){
                    check += '<input type="checkbox" value="' + data.names[i].id + '" checked name="name" disabled /> ' + data.names[i].name + '<br />';
                }
                $('.exp_title p').html(check);
                
                check = ''
                if(data.country.length){
                    for(i in data.country){
                        $('.cntry_block').html($('select[name="cntry"]').hide())
                        check += '<input type="checkbox" value="' + data.country[i].id + '" checked name="country" />' + data.country[i].name + '<br />';
                    }
                    $('.exp_country p').html(check);
                }else{
                    $('.exp_country p').html($('select[name="cntry"]').show());
                }
                
                check = ''
                for(i in data.genre){
                    check += '<input type="checkbox" value="' + data.genre[i].id + '" checked name="genre" />' + data.genre[i].name + '<br />';
                }
                $('.exp_genre p').html(check);
                
                $('.exp_year p').html('<input type="checkbox" value="' + data.year + '" checked name="year" /> ' + data.year);

                check = ''
                if(data.persons.length){
                    $('.exp_person').show();
                    for(i in data.persons){
                        check += ' <input type="checkbox" value="' + data.persons[i].id + '" checked name="persons" /> ' + data.persons[i].name + ' (' + data.persons[i].action + ')<br />';
                    }
                    $('.exp_person p').html(check);
                }else{
                    $('.exp_person p').html('');
                    $('.exp_person').hide();
                }
                
                $('.exp_imdb p').html('<input type="checkbox" value="' + data.imdb + '" checked name="imdb" disabled /> ' + data.imdb);
                if(data.imdb_rate){
                    $('.exp_imdb p').append('<br /><input type="checkbox" value="' + data.imdb_rate + '" checked name="imdb_rate" /> ' + data.imdb_rate);

                    $('.exp_imdb p').append('<br /><input type="checkbox" value="' + data.imdb_votes + '" checked name="imdb_votes" /> ' + data.imdb_votes);
                }
                
                check = ''
                if(data.distr.length){
                    $('.exp_distr').show();
                    for(i in data.distr){
                        check += ' <input type="checkbox" value="' + data.distr[i].id + '" checked name="distr" /> ' + data.distr[i].name + '<br />';
                    }
                    $('.exp_distr p').html(check);
                }else{
                    $('.exp_distr p').html('');
                    $('.exp_distr').hide();
                }
                
                if(data.runtime){
                    $('.exp_runtime').show()
                    $('.exp_runtime p').html('<input type="checkbox" value="' + data.runtime + '" checked name="runtime" /> ' + data.runtime);
                }else{
                    $('.exp_runtime p').html('');
                    $('.exp_runtime').hide();
                }
                
                if(data.budget.length){
                    $('.exp_budget').show()
                    $('.exp_budget p').html('<input type="checkbox" value="' + data.budget[0].id + '" checked name="budget" /> ' + data.budget[0].sum + ' ' + data.budget[0].cur);
                }else{
                    $('.exp_budget p').html('');
                    $('.exp_budget').hide();
                }
                if(data.limit){
                    $('.exp_limit').show()
                    $('.lmts_block').html($('select[name="lmts"]').hide())
                    $('.exp_limit p').html('<input type="checkbox" value="' + data.limit + '" checked name="limit" /> +' + data.limit);
                }else{
                    $('.exp_limit p').html($('select[name="lmts"]').show());
                }
                
                if(data.poster){
                    $('.exp_poster').show()
                    $('.exp_poster p').html('<input type="text" value="http://kinoinfo.ru' + data.poster + '" size="40" /><br /><img src="' + data.poster + '" width="100">');
                }else{
                    $('.exp_poster p').html('');
                    $('.exp_poster').hide();
                }
                
                $(".exp_film_block span").html('');
                $('.exp_f').show();
            }
        }
    }else{
        $(".exp_film_block span").html('Фильм не найден');
    }
}

function get_film_genres_callback(data){
    if(data.status == true){
        $('.film_genres_fields').hide()
        $('.film_genres').html(data.genres + ', ').show()
        for(i in data.content){
            $('.film_genres_field').each(function(){
                if($(this).val() == data.content[i].name){
                    $(this).attr('id', data.content[i].id)
                }
            })
        }
    }
}

function get_film_countries_callback(data){
    if(data.status == true){
        $('.film_countries_fields').hide()
        $('.film_countries').html(data.content + ', ').show()
    }
}

function create_imdb_callback(data){
    if(data.status == true){
        location.reload()
    }
}

function exist_imdbfilm_callback(data){
    if(data.status){
        if(data.redirect){
            var domain = window.location.host;
            window.location.href = 'http://' + domain + '/film/' + data.redirect + '/';
        }else{
            $.fancybox.close()
        }
    }
}

function opinion_remove(id){
    if(confirm("Удалить отзыв?")){
        Dajaxice.film.opinion_remove(function(){location.reload()}, {'id': id})
    }
}

$(document).delegate('.exist_imdbfilm_btn', 'click', function(){
    var current = $('.film_id').attr('id')
    var exist = $('#exist_imdbfilm').val()
    var atype = $('input:radio[name="rb1"]:checked').val()
    if(atype){
        Dajaxice.film.exist_imdbfilm(exist_imdbfilm_callback, {'current': current, 'exist': exist, 'atype': atype})
    }
});

$(document).delegate('.remove_online_player', 'click', function(){
    var val = $('.remove_online_player').attr('id').split('__')
    Dajaxice.film.remove_online_player(remove_online_player_callback, {'id': val[0], 's': val[1]})
});
    
$(document).delegate('.edit_persons_name_btn', 'click', function(){
    var name = $('.pe_name').val()
    var name_id = $('.pe_name').attr('id')
    var person_id = $('.pe_type').attr('id')
    var type = $('.pe_type').val()
    if(name){
        Dajaxice.film.edit_persons_name(false, {'person': person_id, 'name': name, 'id': name_id, 'ntype': type})
        $('#' + person_id + '__' + name_id + '__' + type).html(name)
        $('#' + person_id + '__' + name_id + '__' + type).parent().css({'background': ''})
        $.fancybox.close()
    }
    
});


$(document).delegate('.double_select', 'click', function(){
    var obj = $('input[name="fdoubles"]:checked')
    obj = typeof obj !== 'undefined' ? obj : ''
    if(obj){
        Dajaxice.film.doubles_fix(get_exp_film_callback, {'val': obj.val(), 'imdb': obj.attr('id')});
    }
});

$(document).delegate('.source_f_edit', 'click', function(){
    var img = $('.source_f_img').attr('src')
    var name = $('.source_f_name').text()
    var note = $('.source_f_note').text()
    var txt = '<div class="source_f_block">Название:<br /><input type="text" value="' + name + '" name="name" size="70" /><br />Постер:<br /><input type="text" value="' + img + '" name="img" size="70" /><br />Описание:<br /><textarea name="note" rows="13" cols="70">' + note + '</textarea></div><input type="submit" value="Сохранить на Киноафишу" class="source_f_btn" />'
    $.fancybox.open(txt)
});

$(document).delegate('.source_f_btn', 'click', function(){
    var name = $("input[name='name']").val()
    var note = $("textarea[name='note']").text()
    var kid = $("input[name='kid']").val()
    var domain = window.location.host
    $.fancybox.open('Сохранение...')
    Dajaxice.film.source_create_rel(function(){window.location.href = "http://" + domain + '/film/' + kid}, {'kid': kid, 'name': name, 'note': note})
});

$(document).delegate('.force_film_create', 'click', function(){
    $('.film_new_form_data').submit()
});

$(document).delegate('.create_imdb', 'click', function(){
    var imdb_id = $(this).attr('id')
    var year = $('#imdb_year').text()
    var id = $('input:radio[class="radio_checker"]:checked').val()
    $.fancybox.open($(".exp_film_block").show())
    $('.exp_f').hide()
    if(id){
        $(".exp_film_block span").html('Загрузка...')
        Dajaxice.film.create_imdb(get_exp_film_callback, {'imdb_id': imdb_id, 'id': id, 'year': year})
    }else{
        $(".exp_film_block span").html('<h1>Сначала выберите один фильм из списка!</h1>')
    }
});

$(document).delegate('.imdb_url_btn', 'click', function(){
    var url = $('.imdb_url').val().split('imdb.com/title/tt')
    var id = url[1].split('?')[0].replace('/','')
    var name = $(this).attr('id')
    var year = $('.film_year').text().replace('(','').replace(')','')
    imdb_search(name, year, 'false', id);
});

$(document).delegate('.search_imdb_more', 'click', function(){
    var imdb_id = $(this).attr('id')
    var year = $('#imdb_year').text()
    var name = $(this).parent().find('a').text()
    var kid = $('.film_id').attr('id')
    $.fancybox.open($(".exp_film_block").show())
    $('.exp_f').hide()
    $(".exp_film_block span").html('Загрузка...')
    Dajaxice.film.imdb_search2(get_exp_film_callback, {'imdb_id': imdb_id, 'name': name, 'year': year, 'kid': kid})
});

$(document).delegate('.film_genres_accept_btn', 'click', function(){
    var id = $('.film_id').attr('id')
    var arr = []
    $('.film_genres_field').each(function(){
        val = $(this).attr('value')
        gid = $(this).attr('id')
        gid = typeof gid !== 'undefined' ? gid : '';
        arr.push(val + ';' + gid)
    });
    Dajaxice.film.get_film_genres(get_film_genres_callback, {'id': id, 'arr': arr})
});

$(document).delegate('.film_countries_accept_btn', 'click', function(){
    var id = $('.film_id').attr('id');
    var arr = []
    $('.film_countries_field').each(function(){
        val = $(this).attr('value');
        if(val){
            arr.push(val);
        }
    });
    Dajaxice.film.get_film_countries(get_film_countries_callback, {'id': id, 'arr': arr});
});

$(document).delegate('.film_runtime_accept_btn', 'click', function(){
    var id = $('.film_id').attr('id');
    var isnum = false
    var val = $('.film_runtime_field').val()
    if(val){
        isnum = /^\d+$/.test(val);
    }
    if(isnum){
        Dajaxice.film.get_film_runtime(false, {'id': id, 'val': val});
        $('.film_runtime_fields').hide();
        if(val){
            val = val + ' мин.'
        }
        $('.film_runtime').html(val).show();
    }else{
        alert('Введите число');
    }
});

$(document).delegate('.film_year_accept_btn', 'click', function(){
    var id = $('.film_id').attr('id');
    var val = $('.film_year_field').val()
    if(val){
        isnum = /^\d+$/.test(val);
        if(isnum){
            if(val.length == 4){
                Dajaxice.film.get_film_year(false, {'id': id, 'val': val});
                $('.film_year_fields').hide();
                $('.film_year').html('(' + val + ')').show();
            }else{
                $('.year_err').html('Введите год из 4 цифр');
            }
        }else{
            $('.year_err').html('Введите число');
        }
    }else{
        $('.year_err').html('Введите год');
    }
});

$(document).delegate('.film_name_accept_btn', 'click', function(){
    var id = $('.film_id').attr('id');
    var val = $('.film_name_field').val();
    if(val){
        Dajaxice.film.get_film_name(false, {'id': id, 'val': val});
        $('.film_name_fields').hide();
        $('.film_name').html(val).show();
    }else{
        $('.name_err').html('Введите название');
    }
});

/* end Film */

/* begin Forum */
$(document).ready(function(){
    $('.branding_banner_edit').click(function(){
        $('.branch_title').html('Изменить баннер')
        $('.branch_data').html('')
        $('.bl_branding_string_edit').hide()
        $('.bl_branding_banner_edit').show()
    });
    
    $('.branding_string_edit').click(function(){
        $('.branch_title').html('Изменить бегущую строку')
        $('.branch_data').html('')
        $('.bl_branding_banner_edit').hide()
        $('.bl_branding_string_edit').show()
    });
});

$(document).delegate('.wf_del', 'click', function(){
    if(confirm("Вы уверены, что хотите удалить?")){
        var id = $(this).attr('id').replace('wfd_','')
        var topic = $('.topic_id').val()
        Dajaxice.forums.forum_msg_del(forum_msg_del_callback, {'id': id, 'topic': topic})
    }
    return false;
});

$(document).delegate('.wf_reuse', 'click', function(){
    var id = $(this).attr('id').replace('wfr_','')
    var topic = $('.topic_id').val()
    Dajaxice.forums.forum_msg_restore(forum_msg_del_callback, {'id': id, 'topic': topic})
    return false;
});

function forum_msg_del_callback(data){
    if(data.status){
        window.location.replace(data.redirect_to)
    }
}
/* end Forum */

/* begin Person */
$(document).ready(function(){

    $('.new_person_create_btn').click(function(){
        var ru = $('input[name="person_new_name_ru"]').val()
        var en = $('input[name="person_new_name_en"]').val()
        $('.new_person_msg').html('')
        if(ru.replace(/\s+/g, '').length || en.replace(/\s+/g, '').length){
            Dajaxice.person.person_name_detect(person_name_detect_callback, {'ru': ru, 'en': en});
        }else{
            $('.new_person_msg').html('Заполните поле "Имя Фамилия"')
        }
    });

    $('.newemail_accept_btn').click(function(){
        var val = $('input[name="newemail"]').val()
        var id = $('input[name="person_id"]').val()
        if(val.replace(/ /g,'').length){
            $('.newemail_msg').html('')
            Dajaxice.person.get_person_email(get_person_email_callback, {'id': id, 'val': val});
        }
    });

    $('.person_country_accept_btn').click(function(){
        var id = $("input[name='person_id']").val();
        var country = $("select[name='person_country'] option:selected").val();
        var name = $("select[name='person_country'] option:selected").text();
        $('.person_country_fields').hide();
        $('.person_country').html(name).show();
        Dajaxice.person.country(false, {'id': id, 'country': country});
    });

    
    $('.person_born_accept_btn').click(function(){
        var id = $("input[name='person_id']").val()
        var born = $("input[name='person_born']").val()
        $('.person_born_fields').hide()
        if(!born){
            $('.person_born').html('<span style="font-weight: normal;">дата</span>').show()
        }
        Dajaxice.person.born(person_born_callback, {'id': id, 'born': born})
    });

});

function imdb_person_search(pid, name){
    name = typeof name !== 'undefined' ? name : ''
    if(name.replace(/\s+/g, '').length){
        $.fancybox('Загрузка...')
        Dajaxice.person.imdb_person_search(imdb_search_callback, {'pid': pid, 'name': name, 'exist': true})
    }else{
        $.fancybox('Укажите Имя Фамилия (en): <br /><input type="text" class="person_en_name_alt" /> <input type="button" class="accept_person_en_name_alt" value="Поиск" /><input type="hidden" value="' + pid + '" id="pid" />')
    }
}

$(document).delegate('.accept_person_en_name_alt', 'click', function(){
    var name = $('.person_en_name_alt').val()
    var pid = $('#pid').val()
    if(name.replace(/\s+/g, '').length){
        $.fancybox('Загрузка...')
        Dajaxice.person.imdb_person_search(imdb_search_callback, {'pid': pid, 'name': name, 'exist': false})
    }
});

$(document).delegate('.imdb_person_list_select', 'click', function(){
    var url = $('.imdb_person_url').val()
    var val = $(this).attr('id')
    var pid = $('#pid').val()
    if(typeof val === 'undefined'){
        val = url.split('?')[0].split('imdb.com/name/nm')[1].split('/')[0]
    }
    if(val.replace(/\s+/g, '').length){
        $.fancybox('Загрузка...')
        Dajaxice.person.imdb_person_data(imdb_person_data_callback, {'pid': pid, 'id': val})
    }
});

function imdb_person_get_data(pid, id){
    $.fancybox('Загрузка...')
    Dajaxice.person.imdb_person_data(imdb_person_data_callback, {'pid': pid, 'id': id})
}

function imdb_person_data_callback(data){
    if(data.status){
        content = '<div style="width: 600px; font-size: 14px;"><a href="' + data.url + '" target="_blank">' + data.url + '</a><br /><br />'
        if(data.poster){
            content += '<b>Постер</b><br /><img src="' + data.poster + '" width="80"><br />'
            content += '<input type="text" value="' + data.poster + '" size="40" /><br /><br />'
        }
        content += '<b>Место рождения</b><br />'
        if(data.place.length){
            content += data.place + '<br />'
        }
        country_select = data.country > 0 ? 'checked' : ''
        content += '<input type="checkbox" ' + country_select + ' name="imdb_country" /> <select class="imdb_country">'
        for(i in data.countries){
            selected = data.country == data.countries[i].id ? 'selected' : ''
            content += '<option value="' + data.countries[i].id + '" ' + selected + '>' + data.countries[i].name + '</option>'
        }
        content += '</select><br /><br />'
        if(data.birth.length){
            content += '<b>Дата рождения</b><br /><input type="checkbox" value="' + data.birth + '" checked name="imdb_birth" /> ' + data.birth + '<br /><br />'
        }
        sex_select = data.person_sex > 0 ? 'checked' : ''
        content += '<b>Пол</b><br /><input type="checkbox" ' + sex_select + ' name="imdb_sex" /><select class="imdb_sex">'
        for(i in data.sex){
            selected = data.person_sex == data.sex[i].id ? 'selected' : ''
            content += '<option value="' + data.sex[i].id + '" ' + selected + '>' + data.sex[i].name + '</option>'
        }
        content += '</select><br /><br />'
        if(data.bio.length){
            content += '<b>Биография</b><br /><textarea class="imdb_bio" style="display: none;">' + data.bio + '</textarea><input type="checkbox" name="imdb_bio" disabled /> <span style="color: #999;">' + data.short_bio + '</span><br /><br />'
        }
        content += '<input type="button" value="Сохранить" class="imdb_person_data_save" /><input type="hidden" value="' + data.pid + '" id="pid" /></div>'
        $.fancybox(content);
    }
}

$(document).delegate('.imdb_person_data_save', 'click', function(){
    var place = ''
    var birth = ''
    var bio = ''
    var sex = ''
    var pid = $('#pid').val()
    if($('input[name="imdb_country"]').prop('checked')){
        place = $('.imdb_country option:selected').val()
    }
    if($('input[name="imdb_birth"]').prop('checked')){
        birth = $('input[name="imdb_birth"]').val()
    }
    if($('input[name="imdb_sex"]').prop('checked')){
        sex = $('.imdb_sex').val()
    }
    if($('input[name="imdb_bio"]').prop('checked')){
        bio = $('.imdb_bio').val()
    }
    if(place.length || birth.length || bio.length){
        $.fancybox('Загрузка...')
        Dajaxice.person.imdb_person_save(function(data){location.reload()}, {'pid': pid, 'place': place, 'birth': birth, 'bio': bio, 'sex': sex})
    }
});

function person_name_detect_callback(data){
    if(data.status){
        content = ''
        if(data.content.length){
            content = data.content;
            content += '<br /><input type="button" value="Все равно создать" onclick="$(\'.person_create_form_data\').submit();" />';
            $.fancybox(content);
        }else{
            $('.person_create_form_data').submit()
        }
    }
}


function get_person_email_callback(data){
    if(data.msg.length){
        $('.newemail_msg').html(data.msg)
    }else{
        location.reload();
    }
}

function person_born_callback(data){
    if(data.status && data.content.length){
        $('.person_born').html(data.content).show()
    }
}


function new_usr(){
    Dajaxice.user_registration.new_usr(new_usr_callback, {})
}
function new_usr_callback(data){
    $.fancybox.open(data.content)
    $.fancybox.update()
}
$(document).delegate('.new_usr_create', 'click', function(){
    var email = $('.new_usr_email').val()
    var groups = []
    $('.u_groups option:selected').each(function(){
        groups.push($(this).val())
    })
    var sites = []
    $('.sites_edit option:selected').each(function(){
        sites.push($(this).val())
    })
    if(!IsEmail(email)){
        $('.new_usr_email').css({'border': '1px solid red'})
    }else{
        $('.new_usr_email').css({'border': '1px solid #BCBCBC'})
        Dajaxice.user_registration.new_usr(new_usr_callback, {'email': email, 'groups': groups, 'sites': sites})
    }
    
});


/* end Person */

/* begin Music */
$(document).ready(function(){
    $('.audio_title').click(function(){
        var id = $(this).attr('id')
        var title = $(this).text()
        var mtype = $(this).attr('mtype')
        var tags = $(this).parents('tr').find('#tags').text().split(',')
        var html = ''
        var select = '<select id="tr_type">'
        for(i in MUSIC_TYPES){
            var active = ''
            if(MUSIC_TYPES[i][0] == mtype){
                active = ' selected'
            }
            select += '<option value="' + MUSIC_TYPES[i][0] + '" ' + active +'>' + MUSIC_TYPES[i][1] + '</option>'
        }
        select += '</select>'
        
        tags_html = ''
        for(t in tags){
            if(tags[t].length){
                tags_html += '<span class="tg" title="Удалить тег">' + tags[t] + '</span>'
            }
        }
        
        html += '<ul class="ul_pad">'
        html += '<li><b>Название:</b><input type="text" value="' + title + '" size="40" id="tr_title" /></li>'
        html += '<li><b>Тип:</b>' + select + '</li>'
        html += '<li><b>Теги (перечисление через Enter):</b><div id="tagsinput">' + tags_html + '<input type="text" value="" placeholder="Введите теги" /></div></li>'
        html += '</ul>'
        
        html += '<br /><br /><input type="button" class="tr_acc_btn" value="Сохранить" id="tr_btn_' + id + '"/>'
        
        $.fancybox('<div style="font-size: 12px; width: 500px;">' + html + '</div>')
    });
    
    $('.track_rel').click(function(){
        $.fancybox.open($('.organization_editor_fields').show())
        $('.org_stff_result').html('Loading...')
        $('.org_current_stff span').html('')

        var id = $(this).parents('tr').find('.track_edit').attr('id')
        Dajaxice.music.get_rel(get_rel_callback, {'id': id})
    });
    
    $('.proj_director_name_edit').click(function(){
        var id = $('select[name="director"] option:selected').val()
        var name = $('select[name="director"] option:selected').text()
        $('input[name="director_name"]').val(name)
        $('.proj_director_name_edit_bl').show()
        $.fancybox.update()
    });
    
    $('#proj_director_name_edit_cancel').click(function(){
        $('input[name="director_name"]').val('')
        $('.proj_director_name_edit_bl').hide()
    });
    
    $('.tr_set_relation').click(function(){
        var val = $('input[name="stff_group"]:checked').val()
        var id = $('.organization_id').attr('id')
        var curr_person = $('.org_current_stff').find('a').attr('id')
        val = typeof val !== 'undefined' ? val : ''
        if(val.length && val != id){
            //Dajaxice.organizations.set_org_stff(set_org_stff_callback, {'id': id, 'val': val, 'curr_person': curr_person})
        }
    });
    
    
    $('select[name="artist_char"]').on('change', function(){
        var artist_char = $(this).val()
        $('select[name="artist_select"], select[name="char"]').prop('disabled', true)
        Dajaxice.music.get_artists_by_char(get_artists_by_char_callback, {'artist_char': artist_char})
    });
    
    $('select[name="artist_select"]').on('change', function(){
        var artist = $(this).val()
        $('select[name="char"]').prop('disabled', true)
        Dajaxice.music.get_tracks_by_artist(get_tracks_by_artist_callback, {'artist': artist})
    });
    
    $('.tracks_upload_btn').click(function(){
        
        $('.track_upload_form').each(function(){
            var id = $(this).attr('id').replace('form_','')
            var f = $('#fileInput_' + id).val()
            if(f.length){
                $('input[name="tr_upld_' + id + '"]').click()
            }
        });
    });

    $('.track_upload_btn').click(function(e){

        var id = $(this).parents('.track_upload_form').attr('id').replace('form_','')
        
        var file = $('#fileInput_' + id)[0].files[0]
        
        
        var ext = file.name.split('.').pop()
        exts = ['mp3']
        if($.inArray(ext.toLowerCase(), exts)){
            next = false
            $('#track_upload_progress_' + id).html('Неверный тип файла')
            return false
        }else{
            
            $('#form_' + id).ajaxForm({
                beforeSend: function() {
                    var percentVal = 'Загрузка 0%';
                    $('#track_upload_progress_' + id).html(percentVal);
                },
                uploadProgress: function(event, position, total, percentComplete) {
                    var percentVal = 'Загрузка ' + percentComplete + '%';
                    $('#track_upload_progress_' + id).html(percentVal);
                },
                success: track_upload_callback,
                resetForm: true
            }); 
        }
    });
    

    
 
});
 

function showError(data) { 
    $('#track_upload_progress_' + data.id).html('Ошибка!')
}

function track_upload_callback(data){
    $('#track_upload_progress_' + data.id).html('Загрузка 100%');
}

function track_rel_set(){
    alert(1)
}


function get_artists_by_char_callback(data){
    $('select[name="artist_select"], select[name="char"]').html('')
    $('select[name="artist_select"], select[name="char"]').prop('disabled', false)
    for(i in data.artists) {
        var option = $('<option value="' + data.artists[i].id + '">' + data.artists[i].name__name + '</option>').appendTo('select[name="artist_select"]')
    }
    for(i in data.alphabet) {
        var option = $('<option value="' + data.alphabet[i] + '">' + data.alphabet[i] + '</option>').appendTo('select[name="char"]')
    }
}

function get_tracks_by_artist_callback(data){
    $('select[name="char"]').html('')
    $('select[name="char"]').prop('disabled', false)
    for(i in data.alphabet) {
        var option = $('<option value="' + data.alphabet[i] + '">' + data.alphabet[i] + '</option>').appendTo('select[name="char"]')
    }
}


function get_rel_callback(data){
    var exist = ''
    for(i in data.content){
        exist += '<a href="#" id="" target="_blank">' + data.content[i].title + '</a>'
    }
    if(!exist){
        exist = 'Нет'
    }
    $('.org_current_stff span').html(exist)
    $('.org_stff_result').html('')
    /*
    var html = ''
    for(i in data.content){
        html += '<input type="radio" name="stff_group" value="' + data.content[i].id + '" /> '
        html += '<a href="#" target="_blank">' + data.content[i].name + ' &#8226; <b>' + data.content[i].city + '</b></a> (Phone: ' + data.content[i].phone + '; ' + data.content[i].acc + ')<br />'
    }
    */
    var alpha = ''
    for(i in data.alphabet_filter){
        alpha += '<a href="#" style="padding: 3px; border: 1px solid #CCC; font-size: 11px;">' + data.alphabet_filter[i] + '</a> '
    }
    $('.org_stff_alphabet').html(alpha)
    //$('.org_stff_result').html(html)
    
    
    
}


function set_track_name_callback(data){
    $obj = $('#tp_' + data.id)
    $obj.html(data.mtype)
    $obj.parents('tr').find('.audio_title').show().text(data.title)
    $.fancybox.close()
}


$(document).delegate('.tr_acc_btn', 'click', function(){
    var id = $(this).attr('id').replace('tr_btn_','')
    var title = $('#tr_title').val()
    var type = $('#tr_type').val()
    var tags = []
    $('#tagsinput span').each(function(){
        tags.push($(this).text())
    })
    $('#tr_tr_' + id).find('#tags').text(tags)
    
    if(title.replace(/\s+/g, '').length){
        Dajaxice.music.set_track_name(set_track_name_callback, {'id': id, 'title': title, 'mtype': type, 'tags': tags})
    }
});

/* end Music*/

/* begin Organization */
$(document).ready(function(){
    $('.distributor_new_btn').click(function(){
        $name = $('input[name="distributor_name"]')
        var n = $name.val()
        if(n.replace(/\s+/g, '')){
            $(this).parent().submit()
        }else{
            $name.effect('highlight')
        }
    });


    $('.organization_notex').click(function(){
        var id = $(this).attr('id')
        $(this).hide()
        $('.organization_txt_' + id).show()
    });
    
    $('.organization_txt_cancel_btn').click(function(){
        var cl = $(this).parent().parent().attr('class')
        cl = cl.replace(' org_fields','')
        var id = cl.replace('organization_txt_','')
        $('.' + cl).hide()
        $('#' + id).show()
    });
    
    $('.organization_txt_accept_btn').click(function(){
        $(this).parent().submit()
    });

    $('.stff_appoint').click(function(){
        var val = $('input[name="stff_group"]:checked').val()
        var id = $('.organization_id').attr('id')
        var curr_person = $('.org_current_stff').find('a').attr('id')
        val = typeof val !== 'undefined' ? val : ''
        if(val.length && val != id){
            Dajaxice.organizations.set_org_stff(set_org_stff_callback, {'id': id, 'val': val, 'curr_person': curr_person})
        }
    });
    
    $('.org_stff_pset_btn').click(function(){
        var id = $('.organization_id').attr('id')
        var name = $('.org_stff_pname').val()
        var phone = $('.org_stff_pphone').val()
        var email = $('.org_stff_pemail').val()
        if(name.length){
            $('.org_stff_pname').css({'border': '1px solid #BCBCBC'})
            Dajaxice.organizations.set_org_newstff(set_org_stff_callback, {'id': id, 'name': name, 'phone': phone, 'email': email})
        }else{
            $('.org_stff_pname').css({'border': '1px solid red'})
        }
    });
    
});


function org_stff_phone_or_email(type){
    var val = $('.org_stff_' + type).val()
    var id = $('.organization_id').attr('id')
    var curr_person = $('.org_current_stff').find('a').attr('id')
    if(val.length){
        Dajaxice.organizations.org_stff_pe(set_org_stff_callback, {'id': id, 'val': val, 'type': type, 'curr_person': curr_person})
    }
}


function set_org_stff_callback(data){
    if(data.status){
        $('.org_current_stff').find('span').html(data.msg)
        $a = $('.org_current_stff').find('a')
        $a.attr('href', '/user/profile/' + data.contact.id + '/')
        $a.attr('id', data.contact.id)
        $a.html(data.contact.name + ' &#8226; <b>' + data.contact.city + '</b>')
        $('.org_stff_cu').attr('href', '/user/profile/' + data.contact.id + '/')
        $('.org_stff_cu').html(data.contact.name)
        $('.edit_stff_bl').show()
        $('.newstff').hide()
    }
}

$(document).delegate('.org_stff_alphabet a', 'click', function(){
    var char = $(this).text()
    $('.org_stff_result').html('Loading...')
    $('.org_current_stff').find('span').html('')
    Dajaxice.organizations.get_org_stff(get_org_stff_callback, {'char': char})
});

function get_org_stff(){
    $.fancybox.open($('.organization_editor_fields').show())
    $('.org_stff_result').html('Loading...')
    $('.org_current_stff').find('span').html('')
    Dajaxice.organizations.get_org_stff(get_org_stff_callback, {'char': 'a'})
}

function get_org_stff_callback(data){
    var html = ''
    for(i in data.content){
        html += '<input type="radio" name="stff_group" value="' + data.content[i].id + '" /> '
        html += '<a href="/user/profile/' + data.content[i].id + '/" target="_blank">' + data.content[i].name + ' &#8226; <b>' + data.content[i].city + '</b></a> (Phone: ' + data.content[i].phone + '; ' + data.content[i].acc + ')<br />'
    }
    var alpha = ''
    for(i in data.alphabet_filter){
        alpha += '<a href="#" style="padding: 3px; border: 1px solid #CCC; font-size: 11px;">' + data.alphabet_filter[i] + '</a> '
    }
    $('.org_stff_alphabet').html(alpha)
    $('.org_stff_result').html(html)
}

/* end Organization */

/* begin Post */
function comments_remove(comment){
    if(confirm("Вы уверены, что хотите удалить?")){
        var id = $('.comments_block-id').val()
        Dajaxice.user_registration.bpost_remove_comment(bpost_comments_callback, {'id': id, 'comment': comment, 'parent': ''})
    }
}
function event_total_price(){
    var price = $('input[name="event_price"]').val().replace('$','')
    var sess = $('input[name="event_numsess"]').val()
    var result = price * sess
    $('.event_total_price').html(result)
}
$(document).ready(function(){
    $(".send_reminder_email").click(function(){
        var arr = []
        $('input[name="checker"]:checked').each(function(){
            arr.push($(this).val())
        })
        if(arr.length){
            if (confirm("Are you sure?")) {
                $(this).prop('disabled', true)
                Dajaxice.letsgetrhythm.send_reminder_email(send_reminder_email_callback, {'arr': arr})
            }
        }
    });

    $(".send_report_client").click(function(){
        var id = $(this).attr('id')
        $(this).prop('disabled', true)
        $('.report_msg_callback').html('Sending...')
        Dajaxice.letsgetrhythm.send_report_client(send_report_client_callback, {'id': id})
    });
    
    $(".invoice_bank_add").click(function(){
        var name = $('input[name="bank_name"]').val()
        var acc = $('input[name="bank_acc"]').val()
        var id = $('input[name="invoice_id"]').val()
        if(name.length && acc.length){
            Dajaxice.letsgetrhythm.letsget_bank(letsget_bank_callback, {'id': id, 'name': name, 'acc': acc})
        }else{
            $('.invoice_add_bl span').html('Field can not be empty!').show().fadeOut(3000)
        }
    });
                                    
    $('input[name="event_numsess"], input[name="event_price"]').focusout(function(){
        event_total_price()
    });
    $('input[name="event_numsess"], input[name="event_price"]').keyup(function(){
        event_total_price()
    });
    

    $('.event_edit').click(function(){
        var id = $(this).attr('id')
        var name = $(this).attr('title')
        var place = $('.e_place_' + id).attr('id')
        var contact = $('.e_contact_' + id).attr('id').split(';*')
        var contact_info = contact[1].split(';#')
        var date = $('.e_date_' + id).attr('id')
        var time = $('.e_time_' + id).attr('id')
        var ahead_sms = $('.e_ahead_sms_' + id).attr('id')
        var ahead_email = $('.e_ahead_email_' + id).attr('id')
        var sms = $('.e_sms_' + id).prop('checked')
        var email = $('.e_email_' + id).prop('checked')
        var type = $('.e_type_' + id).attr('id')
        var price = $('.e_price_' + id).attr('id').replace('pr__','')
        var bank = $('.e_bank_' + id).attr('id')
        var note = $('.e_note_' + id).val()
        var numsess = $('.e_numsess_' + id).attr('id')
        var invoice = $('.e_invoice_tmpl_' + id).attr('id')
        
        if(contact[0].length){
            var msg = '<a href="/user/profile/' + contact[0] + '/" target="_blank" title="' + contact_info[1] + '">' + contact_info[0] + '</a>'
        }else{
            var msg = '<b>The organization has no staff </b>'
            if(email=='0'){
                msg += '<b style="color: red;">and email</b>'
                next = false
            }
        }

        $('input[name="event_name"]').val(name)
        $('select[name="event_place"]').val(place)
        $('input[name="event_date"]').val(date)
        $('input[name="event_time"]').val(time)
        $('input[name="event_sms"]').prop('checked', sms)
        $('input[name="event_email"]').prop('checked', email)
        $('select[name="time_msg_sms"]').val(ahead_sms)
        $('select[name="time_msg_email"]').val(ahead_email)
        $('select[name="event_type"]').val(type)
        //var price = $('select[name="event_type"] option:selected').attr('id')
        $('input[name="event_price"]').val(price)
        $('select[name="event_bank"]').val(bank)
        $('textarea[name="event_invoice_note"]').val(note)
        $('input[name="edit"]').val(id)
        $('.event_place_contact').html(msg)
        $('input[name="event_numsess"]').val(numsess)
        if(invoice){
            $('.new_events_fields').find('input[name="event_invoice_tmpl"]').each(function(){
                if($(this).val() == invoice){
                    $(this).prop('checked', true)
                }
            })
        }else{
            $('input[name="event_invoice_tmpl"]').first().prop('checked', true)
        }
        $('.new_events_fields').show()
        $('.events_list').hide()
        $('input[name="event_bcr"], input[name="create"], input[name="event_code"]').prop('disabled', true)
        $('.bсr_msg').html('')
        event_total_price()
        //Dajaxice.letsgetrhythm.bcr(bcr_callback, {'id': place, 'next': false, 'event': id})
        Dajaxice.letsgetrhythm.bcr2(bcr_callback2, {'id': place, 'next': false, 'event': id})
    });

    $('select[name="event_type"]').on('change', function(){
        var price = $(this).children(":selected").attr('id')
        $('input[name="event_price"]').val(price)
    });

    $('select[name="event_place"]').on('change', function(){
        var contact = $(this).children(":selected").attr('id').split(';*')
        var contact_info = contact[1].split(';#')
        var email = $(this).children(":selected").attr('class').replace('ev_place__','')
        var next = true
        if(contact[0].length){
            var msg = '<a href="/user/profile/' + contact[0] + '/" target="_blank" title="' + contact_info[1] + '">' + contact_info[0] + '</a>'
        }else{
            var msg = '<b>The organization has no staff </b>'
            if(email=='0'){
                msg += '<b style="color: red;">and email</b>'
                next = false
            }
        }

        $('.event_place_contact').html(msg)
        
        if(next){
            var place_id = $(this).val()
            $('input[name="event_bcr"], input[name="create"], input[name="event_code"]').prop('disabled', true)
            $('.bcr_msg').html('')
            var id = $('input[name="edit"]').val()
            Dajaxice.letsgetrhythm.bcr2(bcr_callback2, {'id': place_id, 'next': true, 'event': id})
        }else{
            $('input[name="create"]').prop('disabled', true)
        }
    });

    $('.add_photos').click(function(){
        $('.organization_slides').show()
    });
    
    $('.g_photo_edit').click(function(){
        var id = $(this).attr('id')
        var title = $(this).parents('.g_photo_el').find('.g_photo_title').text()
        var descr = $(this).parents('.g_photo_el').find('.g_photo_description').text()
        $('input[name="photo_id"]').val(id)
        $('input[name="photo_title"]').val(title)
        $('textarea[name="photo_description"]').val(descr)
        $.fancybox.open($('.photo_edit_form').show())
    });

    $('.gallery_photo_edit').click(function(){
        var id = $('input[name="photo_id"]').val()
        var title = $('input[name="photo_title"]').val()
        var descr = $('textarea[name="photo_description"]').val()
        $(this).prop('disabled', true)
        Dajaxice.base.gallery_photo_edit(gallery_photo_edit_callback, {'id': id, 'title': title, 'descr': descr})
    });

    $('.g_photo_del, .letsget_img_d').click(function(){
        if (confirm("Are you sure?")) {
            var photo = $(this).attr('id');
            Dajaxice.base.gallery_photo_del(gallery_photo_del_callback, {'id': photo})
        }
    });

    $('.create_new_event').click(function(){
        $('input[name="event_name"]').val('Group Drumming Circle')
        $('input[name="event_date"], input[name="event_time"], input[name="event_bcr"], input[name="event_code"]').val('')
        $('input[name="event_sms"]').prop('checked', false)
        $('input[name="event_email"]').prop('checked', true)
        $('select[name="event_place"]').val($('select[name="event_place"] option:first').val())
        $('select[name="time_msg_sms"]').val($('select[name="time_msg_sms"] option:first').val())
        $('select[name="time_msg_email"]').val($('select[name="time_msg_email"] option:last').val())
        $('select[name="event_type"]').val($('select[name="event_type"] option:first').val())
        $('input[name="event_numsess"]').val(1)
        var place_id = $('select[name="event_place"] option:first').val()
        var price = $('select[name="event_type"] option:selected').attr('id')
        $('input[name="event_price"]').val(price)
        var contact = $('select[name="event_place"] option:first').attr('id').split(';*')
        var contact_info = contact[1].split(';#')
        $('.event_place_contact').html('<a href="/user/profile/' + contact[0] + '/" target="_blank" title="' + contact_info[1] + '">' + contact_info[0] + '</a>')
        $('input[name="edit"]').val(0)
        $('.events_list').hide()
        $('.new_events_fields').show()
        $('input[name="event_bcr"], input[name="create"], input[name="event_code"]').prop('disabled', true)
        $('.bcr_msg').html('')
        event_total_price()
        Dajaxice.letsgetrhythm.bcr2(bcr_callback2, {'id': place_id, 'next': true, 'event': ''})
    });

    $('.stage_show_unpaid').click(function(){
        var $parent = $(this).parents('tr')
        var id = $parent.find('input[name="checker"]').val()
        var un = $parent.find('.stage_unpaid').text()
        $('textarea[name="proj_invoice_note"]').val('')
        $('input[name="invoice_num"]').val('')
        $('input[name="stage_id"]').val(id)
        $('input[name="out_amount"]').val(un)
        $.fancybox($('#iig').show())
    });


    
    $('.new_events_cancel_btn').click(function(){
        $('.new_events_fields').hide()
        $('.events_list').show()
        var arr = [$('input[name="event_name"]'), $('input[name="event_price"]'), $('input[name="event_date"]'), $('input[name="event_time"]')]
        for(i in arr){
            arr[i].parent().find('b').css({'color': '#333'})
        }
    });
    
    $('.create_new_project').click(function(){
        $('.new_project_fields').find('input[type="text"]').each(function(){
            $(this).val('')
        });
        $('.new_project_fields').find('.project_member_del').each(function(){
            $(this).next().remove()
            $(this).prev().remove()
            $(this).remove()
        });
        $('.directors').val($(".directors option:first").val())
        $('.members').val($(".members option:first").val())
        $('select[name="project_currency"]').val($('select[name="project_currency"] option:first').val())
        $('input[name="project_email"]').prop('checked', true)
        $('input[name="project_sms"]').prop('checked', false)
        $('input[name="edit"]').val(0)
        $('.events_list').hide()
        $('.new_project_fields').show()
    });
    
    $('.new_project_cancel_btn').click(function(){
        $('.events_list').show()
        $('.new_project_fields').hide()
    });
    
    $('.project_edit').click(function(){
        var $parent = $(this).parents('tr')
        var id = $parent.find('input[name="checker"]').val()
        var name = $(this).text()
        var url = $parent.find('.prjct_url').text()
        var start = $parent.find('.prjct_start').attr('id')
        var release = $parent.find('.prjct_release').attr('id')
        var budget = $parent.find('.prjct_budget_plan').attr('id').split('__')
        var directors = $parent.find('.prjct_directors').attr('id').split(',')
        var members = $parent.find('.prjct_members').text().split(',')
        var notify = $parent.find('.prjct_notify').text().split(',')
        var email = notify[0] == 'True' ? true : false
        var sms = notify[1] == 'True' ? true : false

        $('.new_project_fields').find('input[type="text"]').each(function(){
            $(this).val('')
        });
        
        $('.new_project_fields').find('.project_member_del').each(function(){
            $(this).next().remove()
            $(this).prev().remove()
            $(this).remove()
        });
        
        $('input[name="edit"]').val(id)
        $('input[name="project_name"]').val(name)
        $('input[name="project_url"]').val(url)
        $('input[name="start_date"]').val(start)
        $('input[name="project_budget"]').val(budget[0])
        $('select[name="project_currency"]').val(budget[1])
        $('input[name="release_date"]').val(release)
        $('input[name="project_email"]').prop('checked', email)
        $('input[name="project_sms"]').prop('checked', sms)
        
        for(i in members){
            if(i == 0){
                $('.members').val(members[i])
            }else{
                var m = $('.members').clone().removeAttr('class').addClass('.members' + members[i]).val(members[i])
                $('.members_fields').append(m)
                $('.members_fields').append('<span class="project_member_del" title="Delete" ></span><br />')
            }
        }
        
        for(i in directors){
            if(i == 0){
                $('.directors').val(directors[i])
            }else{
                var m = $('.directors').clone().removeAttr('class').addClass('.directors' + directors[i]).val(directors[i])
                $('.directors_fields').append(m)
                $('.directors_fields').append('<span class="project_member_del" title="Delete" ></span><br />')
            }
        }
        
        classes = ['members', 'directors']
        for(i in classes){
            $('input[name="all' + classes[i] + '"]').val('')
            var members = []
            $('.' + classes[i] + '_fields select').each(function(){
                members.push($(this).val())
            });
            $('input[name="all' + classes[i] + '"]').val(members)
        }
        
        $('.events_list').hide()
        $('.new_project_fields').show()

    });
    
    
    $(".project_member_new").click(function(){
        $parent = $(this).parent()
        var pclass = $parent.attr('class').replace('_fields','')
        mlength = $parent.find('select').length
        if(mlength < 10){
            var m_first = $parent.find('select:first option:first').val()
            var m = $parent.find('select:first').clone().removeAttr('class').addClass(pclass + mlength).val(m_first)
            $('.' + pclass + '_fields').append(m)
            $('.' + pclass + '_fields').append('<span class="project_member_del" title="Delete" ></span><br />')
            
            var members = []
            $parent.find('select').each(function(){
                members.push($(this).val())
            });
            $('input[name="all' + pclass + '"]').val(members)
        }else{
            $(this).remove();
        }
    });
    
    
    $(".tags_cloud_new").click(function(){
        $parent = $(this).parent()
        var $obj1 = $parent.find('div:first .tags_cloud_name').clone().val('')
        var $obj2 = $parent.find('div:first .tags_cloud_size').clone().val('')
        $parent.append($obj1)
        $parent.append(' ')
        $parent.append($obj2)
        $parent.append(' <span class="del-minus tags_cloud_remove" title="Удалить" ></span><br />')
    });

    $('.seo_main_save').click(function(){
        var arr = ''
        $('.tags_cloud_fields').find('.tags_cloud_name').each(function(){
            var name = $(this).val()
            var size = $(this).next().val()
            if(name.replace(/ /g,'').length){
                if(size.replace(/ /g,'').length==0){
                    size = 12
                }
                var val = name + '~' + size + ';'
                arr += val
            }
        });
        $('input[name="tags_cloud_arr"]').val(arr)
        $(this).parent().submit()
    });

    $('.create_new_stage').click(function(){
        $('.new_stage_fields').find('input[type="text"]').each(function(){
            $(this).val('')
        });
        $('input[name="edit"]').val(0)
        $('.stages_list').hide()
        $('.new_stage_fields').show()
    });
    
    $('.new_stage_cancel_btn').click(function(){
        $('.stages_list').show()
        $('.new_stage_fields').hide()
    });
    
    $('.stage_edit').click(function(){
        var $parent = $(this).parents('tr')
        var id = $parent.find('input[name="checker"]').val()
        var name = $(this).text()
        var start = $parent.find('.stage_start').attr('id')
        var release = $parent.find('.stage_end').attr('id')
        var budget = $parent.find('.stage_budget_plan').attr('id')

        $('.new_stage_fields').find('input[type="text"]').each(function(){
            $(this).val('')
        });

        $('input[name="edit"]').val(id)
        $('input[name="stage_name"]').val(name)
        $('input[name="start_date"]').val(start)
        $('input[name="end_date"]').val(release)
        $('input[name="stage_budget"]').val(budget)

        $('.stages_list').hide()
        $('.new_stage_fields').show()

    });
    
    $('.add_translation').click(function(){
        $('.translation_block').show()
        $('#q-i-block').hide()
        $(this).hide()
    });
    
    $('.add_translation_btn_cancel').click(function(){
        $('.translation_block').hide()
        $('#q-i-block, .edit_translation, .add_translation').show()
    });

    $('.edit_translation').click(function(){
        var subject = $('#q-i-subject').text()
        var text = $('#q-i-text').text()
        tags = ''
        $('.question-item-tags').find('.q-i-tag').each(function(){
            tags += '<span class="tg" title="Удалить тег">' + $(this).text() + '</span>'
        });
        $('.translation_block .tagsinput').find('.tg').each(function(){
            $(this).remove()
        });

        $('.translation_block .tagsinput').prepend(tags)
        $('input[name="translation_subject"]').val(subject)
        $('textarea[name="translation_txt"]').val(text)
        $('.translation_block').show()
        $('#q-i-block').hide()
        $(this).hide()
    });

    $('.add_translation_btn').click(function(){
        var subject = $('input[name="translation_subject"]').val()
        var text = $('textarea[name="translation_txt"]').val()
        var tags = ''
        $('.translation_block .tagsinput .tg').each(function(){
            tags += $(this).text() + ';'
        });

        if(subject.replace(/\s+/g, '').length > 1){
            $('input[name="translation_subject"]').css({'border': '1px solid #BCBCBC'})
            if(text.replace(/\s+/g, '').length > 1){
                $('textarea[name="translation_txt"]').css({'border': '1px solid #BCBCBC'})
                $('input[name="translation_tags"]').val(tags)
                $('.translation_block form').submit()
            }else{
                $('textarea[name="translation_txt"]').css({'border': '1px solid red'})
            }
        }else{
            $('input[name="translation_subject"]').css({'border': '1px solid red'})
        }
    });

    $('.add_translation_answer_btn').click(function(){
        var text = $('textarea[name="translation_txt"]').val()

        if(text.replace(/\s+/g, '').length > 1){
            $('textarea[name="translation_txt"]').css({'border': '1px solid #BCBCBC'})
            $('.translation_block form').submit()
        }else{
            $('textarea[name="answer_txt"]').css({'border': '1px solid red'})
        }
    });

    $('.adv_conditions_txt_edit_save').click(function(){
        txt = tinyMCE.getInstanceById('id_text').getContent()
        Dajaxice.base.get_adv_conditions(function(data){$.fancybox(data.content)}, {'txt': txt})
        $('.adv_conditions_txt_edit').hide()
    })
});

$(document).delegate('.u_groups', 'click', function(){
    if($('.site_editor').prop('selected') == true){
        $('.sites_edit').prop('disabled', false)
    }else{
        $('.sites_edit').prop('disabled', true)
        $('.sites_edit').find('option').each(function(){
            $(this).prop('selected', false)
        });
    }
});

$(document).delegate('.adv_conditions_edit', 'click', function(){
    var txt = $('.adv_conditions_txt').html()
    tinyMCE.getInstanceById('id_text').setContent(txt)
    $('.adv_conditions_txt_edit').show()
    $.fancybox.close()
});

$(document).delegate('.tags_cloud_remove', 'click', function(){
    $(this).next().remove()
    $(this).prev().prev().remove()
    $(this).prev().remove()
    $(this).remove()
});


function send_report_client_callback(data){
    $(this).prop('disabled', false)
    if(data.status){
        $('.report_msg_callback').html(data.msg)
        if(data.send){
            $('.report_msg_callback').prop('disabled', true)
        }
    }
}

function send_reminder_email_callback(data){
    $('.send_reminder_email').prop('disabled', false)
    if(data.status){
        $.fancybox(data.msg)
        $('input[name="checker"]:checked').prop('checked', false)
    }
}

function valid_length($el, len){
    if($el.val().replace(/ /g,'').length > len){
        $el.parent().find('b').css({'color': '#333'})
        result = true
    }else{
        $el.parent().find('b').css({'color': 'red'})
        result = false
    }
    return result
}

function stage_add_valid(){
    $name = $('input[name="stage_name"]')
    $sdate = $('input[name="start_date"]')
    $rdate = $('input[name="end_date"]')
    $budget = $('input[name="stage_budget"]')
    
    var name = valid_length($name, 0)
    var sdate = valid_length($sdate, 0)
    var rdate = valid_length($rdate, 0)
    var budget = valid_length($budget, 0)
    
    if(name && sdate && rdate && budget){
        $('#stage_add_frm').submit()
    }
}



$(document).delegate('.members_fields select, .directors_fields select', 'change', function(){
    var pclass = $(this).parent().attr('class').replace('_fields','')
    var members = []
    $('.' + pclass + '_fields select').each(function(){
        members.push($(this).val())
    });
    $('input[name="all' + pclass + '"]').val(members)
});

$(document).delegate('.project_member_del', 'click', function(){
    $(this).next().remove()
    $(this).prev().remove()
    $(this).remove()
    var members = []
    $('.members_fields select').each(function(){
        members.push($(this).val())
    });
    $('input[name="allmembers"]').val(members)
});




function project_add_valid(){
    $name = $('input[name="project_name"]')
    $sdate = $('input[name="start_date"]')
    $rdate = $('input[name="release_date"]')
    $budget = $('input[name="project_budget"]')
    
    var name = valid_length($name, 0)
    var sdate = valid_length($sdate, 0)
    var rdate = valid_length($rdate, 0)
    

    if(/^\d+$/.test($budget.val())){
        $budget.parent().find('b').css({'color': '#333'})
        next = true
    }else{
        $budget.parent().find('b').css({'color': 'red'})
        next = false
    }
    
    if(name && sdate && rdate && next){
        $('#project_add_frm').submit()
    }
}



function calendar_add_valid(){

    $name = $('input[name="event_name"]')
    $price = $('input[name="event_price"]')
    $date = $('input[name="event_date"]')
    $time = $('input[name="event_time"]')

    var name = valid_length($name, 0)
    var price = valid_length($price, 0)
    var date = valid_length($date, 0)
    var time = valid_length($time, 4)
    
    if(name && price && date && time){
        $('#calendar_add_frm').submit()
    }
}

function bcr_callback(data){
    $('input[name="event_bcr"], input[name="event_code"], input[name="create"]').prop('disabled', false)
    var curr_num = data.curr_bcr
    var curr_code = data.curr_code
    var next_num = data.next_bcr
    var next_code = data.next_code
    alert(curr_num)
    if(curr_num.length == 1){
        curr_num = '0' + curr_num
    }
    if(next_num.length == 1){
        next_num = '0' + next_num
    }
    
    var num = curr_num
    var code = curr_code
    var msg = '<b>Current ' + code + '</b>'

    if(data.content.next){
        var curr_codenum = curr_code + '-' + curr_num
        if(curr_codenum == next_code + '-' + next_num){
            var cu = '<span style="color: green;">Current are ' + curr_codenum + '</span>'
        }else{
            if(data.content.warning){
                var cu = '<span style="color: red;">Current ' + curr_codenum + ' is wrong. Click Save.</span>'
            }else{
                var cu = ''
            }
        }
        num = next_num
        code = next_code
        msg = '<b style="color: green;">+1 to previous.</b> ' + cu
    }
    
    $('input[name="event_bcr"]').val(num)
    $('input[name="event_code"]').val(code)
    $('.bсr_msg').html(msg)
    
}


function bcr_callback2(data){
    $('input[name="event_bcr"], input[name="event_code"], input[name="create"]').prop('disabled', false)

    if(data.next){
        var msg = '<b style="color: green;">+1 to previous. </b>'
    }else{
        var msg = '<b>is current. </b>'
    }
    
    if((data.curr_bcr - 1) != data.prev_bcr){
        if(data.prev_bcr != 0){
            msg += ' <span style="color: red;">Previous ' + data.curr_code + ' has been with the number ' + data.prev_bcr + '</span>'
        }else{
            msg += ' <span style="color: red;">Previous ' + data.curr_code + ' does not exist</span>'
        }
        
    }

    $('input[name="event_bcr"]').val(data.curr_bcr)
    $('input[name="event_code"]').val(data.curr_code)

    $('.bсr_msg').html(msg)
    
}



$(document).delegate('.letsget_edit_notes', 'click', function(){
    var id = $(this).attr('id')
    var val = $(this).text()

    var fullsc = $.cookie("fullscreen")
    if(fullsc && fullsc != 'null'){
        $('.letsget_edit_note_val, .letsget_edit_note_btn').css({'font-size': '16px', 'height': '30px'})
    }

    $('.letsget_edit_note_val').val(val)
    $('.letsget_edit_note_val').attr('id', id.replace('__',';'))
    
    $('.letsget_edit_note_val').datepicker("destroy");
    if(id.split('__')[0] == 'note0'){
        $('.letsget_edit_note_val').datepicker({
            altFormat: "yy-mm-dd",
            dateFormat: 'yy-mm-dd',
            changeMonth: true,
            changeYear: true,
            firstDay: 1
        });
    }
    
    $.fancybox.open($('.letsget_edit_note_bl').show())
    $('.letsget_edit_note_val').focus()
});


$(document).delegate(".letsget_edit_note_btn", 'click', function(){
    var id = $('.letsget_edit_note_val').attr('id')
    var val = $('.letsget_edit_note_val').val()
    if(id.split(';')[0] == 'tag'){
        Dajaxice.letsgetrhythm.letsget_edit_tag(letsget_edit_note_callback, {'id': id, 'val': val})
    }else{
        Dajaxice.letsgetrhythm.letsget_edit_note(letsget_edit_note_callback, {'id': id, 'val': val})
    }
});

$(document).delegate('input[name="tmplt"]', 'change', function(){
    var txt = $('.tmplt__' + $(this).val()).html()
    tinyMCE.getInstanceById('id_note').setContent(txt)
});

function letsget_bank_callback(data){
    if(data.status){
        $('select[name="bank"]').html('')
        for(i in data.content){
        var option = $('<option value="' + data.content[i].id + '">' + data.content[i].name + ' | ' + data.content[i].account + '</option>').appendTo('select[name="bank"]')
        }
        $.fancybox.close()
    }
}

function invoice_bank_edit(edit){
    var val = ['', '']
    var id = ''
    if(edit){
        val = $('select[name="bank"] option:selected').text().split(' | ')
        id = $('select[name="bank"] option:selected').val()
    }
    $('input[name="bank_name"]').val(val[0])
    $('input[name="bank_acc"]').val(val[1])
    $('input[name="invoice_id"]').val(id)
    $.fancybox.open($('.invoice_add_bl').show())
}

function invite_files(cl){
    var arr = []
    if(cl){
        var obj = '.panel_list'
    }else{
        var obj = '.events_list'
    }
    $(obj).find('input[name="checker"]:checked').each(function(){
        arr.push($(this).val())
    })
    if(arr.length){
        Dajaxice.letsgetrhythm.invite_files(invite_files_callback, {'itype': 'invite', 'cl': cl, 'arr': arr})
    }
}

function invite_files_callback(data){
    if(data.status){
        var txt = ''
        var html = '<b>Add Files To The Invite Message: </b><br />'
        for(i in data.files){
            html += '<input type="checkbox" name="inv_files" value="' + i + '" /> '
            html += data.files[i][1] + '<br />'
        }
        
        html += '<br /><b>Select Template: </b><br />'
        
        if(!data.text){
            for(i in data.objs){
                html += '<input type="radio" name="tmplt" value="' + data.objs[i].id + '" ' + data.objs[i].check + '/> ' + data.objs[i].title + '<br />'
                html += '<div class="tmplt__' + data.objs[i].id + '" style="display: none;"> ' + data.objs[i].txt + '</div>'
            }
            if(data.objs[0]){
                txt = data.objs[0].txt
            }
            
        }else{
            html += '<input type="radio" name="tmplt" value="' + data.tmpl + '" checked /> ' + data.title + '<br />'
            txt = data.text
            
        }
        
        if(html.length){
            html += '<br /><input type="button" onclick="files_send_invite(' + data.cl + ');" value="Send" id="fsi"/>'
            html += '<span class="loader"></span>'
            html += ' | <a href="/admin/upload-files/">Upload More Files</a> <input type="button" onclick="$(\'.overlay_bl, .files_inv\').hide();" style="float: right;" value="Cancel" /> <input type="hidden" value="' + data.tmpl + '" class="files_inv_tmpl" />'
        }

        tinyMCE.getInstanceById('id_note').setContent(txt)
        
        $('.files_inv .files_inv_data').html(html)
        $('.files_inv, .overlay_bl').show()
    }
}

function files_send_invite(cl){
    var files = []
    $('.files_inv').find('input[name="inv_files"]').each(function(){
        if($(this).prop('checked')){
            files.push($(this).val())
        }
    })
    generate_invoice('invite', false, cl, files)
}


function generate_invoice(name, validate, cl, files){
    files = typeof files !== 'undefined' ? files : [];
    txt = tinyMCE.getInstanceById('id_note').getContent()
    
    var arr = []
    var tmpl = 0
    $('input[name="tmplt"]:checked').each(function(){
        tmpl = $(this).val()
    })
    if(cl){
        var obj = '.panel_list'
    }else{
        var obj = '.events_list'
    }
    $(obj).find('input[name="checker"]:checked').each(function(){
        arr.push($(this).val())
    })
    
    if(arr.length){
        $('#fsi').prop('disabled', true).val('SENDING, Please Wait...')
        $('.loader').css({'display': 'inline-block'})
        Dajaxice.letsgetrhythm.invoice_gen(invoice_gen_callback, {'arr': arr, 'name': name, 'validate': validate, 'cl': cl, 'files': files, 'tmpl': tmpl, 'txt': txt})
    }
    
}

function invoice_gen_callback(data){
    $('.files_inv .files_inv_data').html('')
    $('.files_inv, .overlay_bl').hide()
    if(data.status){
        if(data.type == 'bsb'){
            var html = '<div class="bsb_bl">'
            for(i in data.events){
                html += '<div><b>BSB:</b> <input type="text" value="" size="10" name="bsb" id="' + data.events[i].id + '" /> for <a href="#">' + data.events[i].client__organization__name + '</a>' + data.events[i].id + '</div>'
            }
            html += '<input type="hidden" value="' + data.events[i].arr + '" name="arr" /></div>'
            $.fancybox.open(html)
        }else{
            var html = '<table class="panel_list"><th>Organization</th><th>Contact</th><th>E-mail</th><th>Status</th>'
            if(data.validate){
                html += '<th>PDF</th>'
                html = '<h3>Check Statuses And PDF Files:</h3><br />' + html
            }else{
                html = '<h3>Sending Has Been Completed, Check Statuses:</h3><br />' + html
            }
            for(i in data.log){
                if(data.log[i].status){
                    var style = 'style="color: green;"'
                    $('#tr_' + data.log[i].client_id + ' div:last').addClass('invited')
                }else{
                    var style = 'style="color: red;"'
                }
                
                var download = ''
                if(data.log[i].file_name.length){
                    download = '<a href="/upload/invoices_pdf_tmp/' + data.log[i].file_name + '" target="_blank">download</a>'
                }
                
                html += '<tr><td><div><a href="/org/' + data.log[i].org_slug + '/" target="_blank">' + data.log[i].org_name + '</a></div></td>'
                html += '<td><div>' + data.log[i].link + '</div></td>'
                html += '<td><div>' + data.log[i].email + '</div></td>'
                html += '<td><div ' + style + '>' + data.log[i].msg + '</div></td>'
                if(data.validate){
                    html += '<td><div>' + download + '</div></td></tr>'
                }
            }
            html += '</table>'
            var modal = false
            if(data.validate){
                if(data.objs.length){
                    html += '<br /><b>Select Template: </b><br />'
                }
                for(i in data.objs){
                    html += '<input type="radio" name="tmplt" value="' + data.objs[i].id + '" ' + data.objs[i].check + '/> ' + data.objs[i].title + '<br />'
                }
                html += '<br /><input type="button" value="Send" onclick="generate_invoice(\'invoice\', false, false);" /> | <input type="button" value="Cancel" onclick="$.fancybox.close();" />'
                modal = true
            }
            $('.msg_log').html(html)
            $.fancybox.open($('.msg_log').show(), {'modal': modal})
        }
    }
}

function letsget_edit_note_callback(data){
    if(data.status){
        $('#tr_' + data.id.replace('tag__', '')).css('background', data.color)
        $('#' + data.id).text(data.val)
        $.fancybox.close()
    }
}

function get_org_by_name(){
    var name = $('input[name="new_org"]').val()
    var tag = $('input[name="new_org_tag"]').val()
    if(name.length){
        $('.get_org_by_name').prop('disabled', true).val('Loading ...')
        Dajaxice.organizations.get_org_by_name(get_user_by_phone_callback, {'name': name, 'tag': tag})
    }else{
        $('.get_org_by_name_wrng').html('Field can not be empty!').show().fadeOut(3000)
    }
}

function get_user_by_phone(){
    var phone = $('input[name="new_phone"]').val()
    var tag = $('input[name="new_client_tag"]').val()
    if(phone.length){
        if(/^\d+$/.test(phone)){
            $('.get_user_by_phone').prop('disabled', true).val('Loading ...')
            Dajaxice.user_registration.get_user_by_phone(get_user_by_phone_callback, {'phone': phone, 'tag': tag})
        }else{
            $('.get_user_by_phone_wrng').html('Enter only numbers!').show().fadeOut(3000)
        }
    }else{
        $('.get_user_by_phone_wrng').html('Field can not be empty!').show().fadeOut(3000)
    }
}

function get_user_by_phone_callback(data){
    if(data.status){
        if(data.type == 1){
            $('.exist_users b').html(data.url + ' already exist and has just been added to Client List')
        }else{
            $('.exist_users b').html(data.url + ' created and has just been added to Client List')
        }
        
        if(data.created){
            $el = $('.panel_list tr:last-child')
            $el.after(data.html)
        }
        
        $.fancybox.open($('.exist_users').show())
        $('input[name="new_phone"], input[name="new_org"]').val('')
        $('.get_user_by_phone, .get_org_by_name').prop('disabled', false).val('Create')
    }
}




function get_user_by_email(create){
    var email = $('input[name="new_email"]').val()
    if(email.length){
        $('.get_user_by_email, .create_user_by_email').prop('disabled', true).val('Loading ...')
        Dajaxice.user_registration.get_user_by_email(get_user_by_email_callback, {'email': email, 'create': create})
    }
}

function get_user_by_email_callback(data){
    if(data.status){
        var txt =''
        for(i in data.content){
            var user = data.content[i].fio ? data.content[i].fio : data.content[i].short_name
            txt += '<a href="/user/profile/' + data.content[i].id + '/" target="_blank">' + user + '</a><br />'
        }
        if(data.type == 1){
            $('.exist_users span').html(txt)
            $.fancybox.open($('.exist_users').show())
        }else{
            $('.news_users span').html(txt)
            $('.news_users').show()
            $.fancybox.close()
        }
        $('.get_user_by_email').val('Create')
        $('.create_user_by_email').val('No, create new user')
        $('.get_user_by_email, .create_user_by_email').prop('disabled', false)
    }
}

function gallery_photo_del_callback(data){
    if(data.status){
        $('#g' + data.id).remove()
    }
}

function gallery_photo_edit_callback(data){
    if(data.status){
        var title = $('#g' + data.id).find('.g_photo_title')
        title.text(data.title)
        var descr = $('#g' + data.id + ' .g_photo_description')

        if(descr.length){
            descr.text(data.descr)
        }else{
            title.after('<p class="g_photo_description">' + data.descr + '</p>')
        }
        $.fancybox.close()
        $('.gallery_photo_edit').prop('disabled', false)
    }
}

function e_past_info(id){
    Dajaxice.base.e_past_info(e_past_info_callback, {'id': id})
}

function e_past_info_callback(data){
    if(data.status){
        txt = '<tr><td><div><b>Client:</b></div></td><td colspan="3"><div>' + data.content.link + '</div></td>'
        txt += '<tr><td><div><b>E-Mail:</b></div></td><td colspan="3"><div>' + data.content.client_email + '</div></td>'
        txt += '<tr><td colspan="4"><div></div></td>'
        txt += '<tr><td><div><b>Sent SMS:</b></div></td><td><div>' + data.content.e_sms_notified + '</div></td><td>' + data.content.e_sms_status + '</td><td><div>' + data.content.e_sms_dtime + '</div></td>'
        txt += '<tr><td><div><b>Sent e-mail:</b></div></td><td><div>' + data.content.e_email_notified + '</div></td><td>' + data.content.e_email_status + '</td><td><div>' + data.content.e_email_dtime + '</div></td>'
        txt += '<tr><td><div><b>Sent invite:</b></div></td><td><div>' + data.content.e_invite_notified + '</div></td><td>' + data.content.e_invite_status + '</td><td><div>' + data.content.e_invite_dtime + '</div></td>'
        txt += '<tr><td><div><b>Sent invoice:</b></div></td><td><div>' + data.content.e_invoice_notified + '</div></td><td>' + data.content.e_invoice_status + '</td><td><div>' + data.content.e_invoice_dtime + '</div></td>'
        $('#e_past_info_bl').html('<table class="panel_list">' + txt + '</table>')
        $.fancybox.open($('#e_past_info_bl').show())
    }
}

/*
function e_past_info_callback(data){
    if(data.status){
        var txt = ''
        for(i in data.content){
            txt += '<tr><td><div><a href="/user/profile/' + data.content[i].id + '/" target="_blank">' + data.content[i].name + '</a></div></td><td><div>' + data.content[i].e_sms_notified + '</div></td><td><div>' + data.content[i].e_sms_status + '</div></td><td><div>' + data.content[i].e_email_notified + '</div></td><td><div>' + data.content[i].e_email_status + '</div></td></tr>'
        }
        $('#e_past_info_bl').html('<table class="panel_list"><th>Client</th><th>SMS Notified</th><th>SMS Status</th><th>E-mail Notified</th><th>E-mail Status</th>' + txt + '</table>')
        $.fancybox.open($('#e_past_info_bl').show())
    }
}*/


/* end Post */

/* begin show_parsed_data */

$(document).ready(function(){
    count = 0;
    $('#parse_data').val("Разобрать");

    $('#parse_data').click(function(){
        check = 0;
        if($('#checkParseAll').is(':checked')){
            count = 0;
            check = 1;
            $('#info').html('').html("функция считает и запишет в модель все записи из дампа, ожидайте...");
        }else{
            count += 1;
            $('#info').html('').html("считываем " + count + " запись, ожидайте...");
        }

        Dajaxice.movie_online.parse_data_show(parse_show_callback, {'count': count, 'check': check});

        $('#all_cheker').hide();
        $('#show_parse').hide();
        $('#parse_data').hide();
        $('#show_filters').hide();
        $('#show_img').hide();
        $('#show_timer').hide();
    });
});


function parse_show_callback(data){
    if (data.check == 0){
        $('#parse_data').show();
        $('#parse_data').val("Считать еще");

        $('#info').html('').html("Результат: <br />____________________________________");

        $('#show_img').show();
        $('#show_img').html('').html('<div  style="float: right; margin-right: 5px;"><img src="'+data.poster_thumbnail+'"></div>');

        $('#show_parse').show();
        $('#show_parse').html('').html(data.pased_data);

        $('#show_filters').show();
        $('#show_filters').html('').html("____________________________________<br />фильтрация:   serial = 'False' and type_f = 'FILM'");

        $('#show_timer').show();
        $('#show_timer').html('').html("Время 1 шага - 'загрузка данных': "+data.timer1+" | 2 шага - 'чтение/запись в модель': "+data.timer2+" | Итоговое время: "+data.timerf);
    }

    if (data.check == 1){
        if (data.cnt_in_model == 0){
            $('#info').html('').html("Результат: Новых данных нет. Обработка запроса заняла: "+data.timerf);
        }else{
            $('#info').html('').html("Результат: Все данные записанны в модель, новых записей: "+data.cnt_in_model+". Обработка запроса заняла: "+data.timerf);
        }
    }

    if (data.error == 'error'){
        $('#info').html('').html("Ошибка: отсутствует файл дампа мегого");
    }

}
/* end show_parsed_data */



/* begin ident_parsed_data */

$(document).delegate('#ident_button', 'click', function(){

    $('#film_info').hide();
    $('#ident_menu').hide();
    $('#ident_select').hide();
    $('#ident_button').hide();
    $('#all_cheker').hide();

    $('#info').html('').html("идентификация, ожидайте...");

    if($('#checkIdentAll').is(':checked')){
        Dajaxice.movie_online.parse_data_ident(parse_ident_callback, {'selected':"All"});
    }else{
        var selected = $("#ident_select option:selected").val();
        Dajaxice.movie_online.parse_data_ident(parse_ident_callback, {'selected':selected});
    }

});

function parse_ident_callback(data){

    $('#ident_menu').show();
    $('#film_info').show();
    $('#ident_select').show();
    $('#ident_button').show();
    $('#all_cheker').show();

    if (data.request_type == 1){
        $('#info').html('').html('<strong>Все фильмы прошли идентификацию </strong> <br /> Итоговое время выполнения функции: '+data.timer);
        $('#film_info').hide();
        $('#ident_menu').hide();
        $('#film_info').hide();
        $('#ident_select').hide();
        $('#ident_button').hide();
        $('#all_cheker').hide();
    }

    if (data.request_type == 0){
        if (data.kid){
            $('#info').html('').html('<strong>info:</strong> <font color="#228B22"> '+data.info + "</font> <strong> ID:</strong> " + data.kid +" <strong> Итоговое время выполнения функции:</strong> "+data.timer);
            get_film(data.kid);
            $('#film_info').hide();
        }else{
            $('#info').html('').html('<strong>info:</strong> <font color="#B22222"> '+data.info + "</font> <strong> ID:</strong> " + data.kid +" <strong> Итоговое время выполнения функции: "+data.timer+"</strong>");
            $('#film_info').hide();
        }
    }

}

/* end ident_parsed_data */

