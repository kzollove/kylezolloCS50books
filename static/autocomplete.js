//Pass text between autocomplete and submit fields
$("input").keyup(function() {
    $("input").val($(this).val())
    M.updateTextFields();
})
//Show/hide autocomplete and submit based on checkbox
$(document).ready(function() {
    $("#auto").hide()  
    $("#queryReturn").hide()
})

$("#autoCheck").click(function() {
    if ($("#autoCheck").is(":checked")) {
        $("#searchForm").hide()
        $("#auto").show()
        $("#queryReturn").show()

    } else {
        $("#searchForm").show()
        $("#auto").hide()
        $("#queryReturn").hide()    
    }
});

//http://davidwalsh.name/javascript-debounce-function
function debounce(func, wait, immediate) {
    var timeout;
    return function() {
        var context = this, args = arguments;
        var later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        var callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(context, args);
    };
};

//Autocomplete functionality
function autoComp() {

        //Send value and name attr of input as single get request
        $.get('/search?q=' + $(this).val(), function(data) {
            let html = ''
            const keys =  Object.keys(data)
            for (key of keys) {
                html += '<li><h6><a href="/bookpage?info=' + key + ',' + data[key]['author'] + ',' + data[key]['year'] + ',' + data[key]['isbn'] + ',' + data[key]['id'] + '">' + key +  '</a></h6><p>' + data[key]['author'] + '; ' + data[key]['year'] + '</p></li>'
            }
            $("#queryReturn").html(html);
        });
};

//Fire autocomplete on keyup or when autcomplete is selected (second argument is search delay time)
$("input").keyup(debounce(autoComp, 250))

