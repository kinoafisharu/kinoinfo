
$( document ).ready(function() {
    $( ".hamburger-mobile" ).show();
    $( ".hamburger-mobile" ).click(function() {
        $( ".menu-mobile" ).slideToggle( "slow", function() {
            $( ".hamburger-mobile" ).hide();
            $( ".cross-mobile" ).show();
        });
    });
    $( ".cross-mobile" ).click(function() {
        $( ".menu-mobile" ).slideToggle( "slow", function() {
            $( ".cross-mobile" ).hide();
            $( ".hamburger-mobile" ).show();
        });
    });
});


var pageWidth, pageHeight;

var previousCheckOrientation = -1;
var currentCheckOrientation = 1;

var basePageWidth = {
    width: 320,
    height: 515,
    scale: 1,
    scaleX: 1,
    scaleY: 1
};

var basePage = Object.assign({}, basePageWidth);


var pageWidthHeader, pageHeightHeader;

var baseHeader = {
    width: 500,
    height: 40,
    scale: 1,
    scaleX: 1,
    scaleY: 1
};

$(function(){
    owlOptions = {
        //loop:true,
        margin: 0,
        nav: true,
        items: 1,
        responsiveClass: false,
        navigation : true,
        singleItem:true,
        autoWidth: false,
        responsive: false,
        dots:false,
        slideTransition: 'linear',
    }
    //var owlObj = $('.owl-carousel');
    //var owlActive = owlObj.owlCarousel(owlOptions)

    var objFlick = $('.main-carousel');
    var objFlickActive = objFlick.flickity({
        freeScroll: true,
        contain: true,
        prevNextButtons: false,
        pageDots: false
    });

    var $page = $('.page_content');
    var $rowHeader = $('#row-header');

    getHeaderSize();
    scaleHeaderPages($rowHeader, pageWidthHeader, pageHeightHeader);

    getPageSize();
    scalePages($page, pageWidth, pageHeight);

    //using underscore to delay resize method till finished resizing window
    $(window).resize(_.debounce(function () {
        getPageSize();
        scalePages($page, pageWidth, pageHeight);
    }, 150));

    function getPageSize() {
        pageHeight = $('#container').height();
        pageWidth = $('#container').width();
    }

    function baseScalePages(page, maxWidth, maxHeight) {
        var scaleX = 1, scaleY = 1;
        scaleX = maxWidth / basePage.width;
        scaleY = maxHeight / basePage.height;
        basePage.scaleX = scaleX;
        basePage.scaleY = scaleY;
        basePage.scale = (scaleX > scaleY) ? scaleY : scaleX;

        var newLeftPos = Math.abs(Math.floor(((basePage.width * basePage.scale) - maxWidth)/2));
        var newTopPos = Math.abs(Math.floor(((basePage.height * basePage.scale) - maxHeight)/2));

        return [newLeftPos, newTopPos];
    }
    function scalePages(page, maxWidth, maxHeight) {
        var resultCurrentOrientation = $(window).width() < $(window).height();
        //owlObj.trigger('refresh.owl.carousel');
        objFlickActive.show()
            .flickity('resize')

        if(resultCurrentOrientation) {
            $("#mainRow").css({"display": ""});
            $("#mainRow2").css({"display": "none"});
            basePage.height = basePageWidth.height;
            basePage.width = basePageWidth.width;
        } else {
            $("#mainRow").css({"display": "none"});
            $("#mainRow2").css({"display": ""});
            basePage.width = (basePageWidth.width * 3);
            basePage.height = basePageWidth.height;
        }

        //if (previousCheckOrientation != currentCheckOrientation){
        //    if(resultCurrentOrientation) {
        //        $("#mainRow").css({"display": ""});
        //        $("#mainRow2").css({"display": "none"});
        //        basePage.height = basePageWidth.height;
        //        basePage.width = basePageWidth.width;
        //    } else {
        //        $("#mainRow").css({"display": "none"});
        //        $("#mainRow2").css({"display": ""});
        //        basePage.width = (basePageWidth.width * 3);
        //        basePage.height = basePageWidth.height;
        //    }
        //}
//
        //previousCheckOrientation = currentCheckOrientation;
        //if(resultCurrentOrientation) {
        //    currentCheckOrientation = 1;
        //} else {
        //    currentCheckOrientation = 0;
        //}

        var result = baseScalePages(page, maxWidth, maxHeight);
        var newLeftPos = result[0];
        var newTopPos = result[1];
        page.attr('style', '-webkit-transform:scale(' + basePage.scale + '); left: ' + newLeftPos + 'px; top:' + newTopPos + 'px;');
    }

    //using underscore to delay resize method till finished resizing window
    $(window).resize(_.debounce(function () {
        getHeaderSize();
        scaleHeaderPages($rowHeader, pageWidthHeader, pageHeightHeader);
    }, 150));

    function getHeaderSize() {
        pageHeightHeader = $('#header-select').height();
        pageWidthHeader = $('#header-select').width();
    }

    function scaleHeaderPages(page, maxWidth, maxHeight) {
        var scaleX = 1, scaleY = 1;
        scaleX = maxWidth / baseHeader.width;
        scaleY = maxHeight / baseHeader.height;
        baseHeader.scaleX = scaleX;
        baseHeader.scaleY = scaleY;
        baseHeader.scale = (scaleX > scaleY) ? scaleY : scaleX;

        page.attr('style', '-webkit-transform:scale(' + baseHeader.scale + ');');
    }
});

