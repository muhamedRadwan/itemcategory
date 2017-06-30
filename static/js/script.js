/**
 * Created by Mohamed-A.Radwan on 28/06/2017.
 */
function signInCallback(authResult){
    if(authResult['code']){
        $('#signInButton').attr('style','display:none');
        $.ajax({
            type:'post',
            url:'/gconnect?state={{STATE}}',
            processDate:false,
            contentType:'application/octet-stream; charset=utf-8',
            data:authResult['code'],
            success: function(result) {
                // Handle or verify the server response if necessary.
                if (result) {
                    $('#result').html('Login Successful!</br>' + result + '</br>Redirecting...')
                    setTimeout(function () {
                        window.location.href = "/restaurants";
                    }, 4000);

                } else if (authResult['error']) {
                    console.log('There was an error: ' + authResult['error']);
                } else {
                    $('#result').html('Failed to make a server-side call. Check your configuration and console.');
                }
            }
        });
    }
}
function sendTokenToServer() {
var access_token = FB.getAuthResponse()['accessToken'];
console.log(access_token)
console.log('Welcome!  Fetching your information.... ');
FB.api('/me', function(response) {
  console.log('Successful login for: ' + response.name);
 $.ajax({
  type: 'POST',
  url: '/fbconnect?state={{STATE}}',
  processData: false,
  data: access_token,
  contentType: 'application/octet-stream; charset=utf-8',
  success: function(result) {
    // Handle or verify the server response if necessary.
    if (result) {
      $('#result').html('Login Successful!</br>'+ result + '</br>Redirecting...')
     setTimeout(function() {
      window.location.href = "/categories/";
     }, 4000);

  } else {
    $('#result').html('Failed to make a server-side call. Check your configuration and console.');
     }
  }

});
});
}