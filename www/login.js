
function doLogin() {

    var username = $('#username').val();
    var password = $('#password').val();

    $.ajax(
    {
        type: "POST",
        url: "/login" ,
//        data: {stuff_for_python: document.getElementById("Uname").value},
        data: {'username': username, 'password': password},
        success: function(response)
        {
            console.log(response);
            if ( response == "Failed!" )
            {
                toastr.error("Login Failed!");
            }
            else if ( response == "Succeed!")
            {
                var curURL = window.location.href;
                curURL = curURL.replace("login", "lendingbot");
                console.log(curURL);
                window.location.replace(curURL);
                
            }
                
//                window.open("localhost:8000/lendingbot.html","_self")
//                window.location = "localhost:8000/lendingbot.html";
        },
        error: function(data)
        {
            alert(data.responseText);
        },
    });
}

$(document).ready(function () {
    toastr.options = {
        "positionClass": "toast-bottom-center",
        "timeout": "1000"
    }
});
