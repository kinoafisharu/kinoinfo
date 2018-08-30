function isOverflowed(el){
    return el.prop('scrollHeight') > el.prop('clientHeight') || el.prop('scrollWidth') > el.prop('clientWidth');
}

$(document).ready(function(){

    $('.widget_schedule__content__data').hover(
        function(){
            css_height = $(this).prop('scrollHeight') + 'px'
            if(isOverflowed($(this))){
                $(this).css('overflow', 'visible');
                //$(this).css('border', '1px solid #DBDBDB');
                $(this).css('position', 'absolute');
                $(this).css('height', css_height);
                $(this).css('background', '#FFF');
                $(this).css('right', '0');
                $(this).css('box-shadow', '0 0 5px #000');
            }
        },
        function(){
            css_height = $('.widget_schedule__height').val() + 'px';
            $(this).css('position', 'static');
            $(this).css('overflow', 'hidden');
            //$(this).css('border', '1px solid #F0F0F0');
            $(this).css('height', css_height);
            $(this).css('background', 'inherit');
            $(this).css('box-shadow', 'none');
        }
        );


});


