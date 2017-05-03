var internal_api = 'http://0.0.0.0:5000'
var state = window.location.pathname.replace('/', '').toLowerCase()
var legis_url =  internal_api + '/us/'+ state + '/reps'

fetch(legis_url)
    .then(res => res.json())
.then((out) => {
    console.log('Checkout this JSON! ', out);
var state_view = new Vue({
    el: '#state-legislators',
    data: {
        legis: out
    }
});
})
.catch(err => console.error(err));


fetch(internal_api + '/' + state + '/upcoming_bills')
    .then(res => res.json())
.then((out) => {
    console.log("upcoming bills json", out);
var bills_state = new Vue({
    el: '#bill-data',
    data: {
        bills: out
    }
});
})
.catch(err => console.error(err));

$(document).ready(function() {
    $('.expander-trigger').click(function(){
        $(this).toggleClass("expander-hidden");
    });
});