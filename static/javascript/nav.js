
function openNav() {
    document.getElementById("mySidenav").style.width = "250px";
}

function closeNav() {
    document.getElementById("mySidenav").style.width = "0";
}


$('#myModal').on('shown.bs.modal', function () {
  $('#myInput').focus()
})

//function deleteconfirmation(){
//var deletebutton = document.getElementById("delete");
//var condelete = document.getElementById("deleteButton");
//
//var test = condelete.getAttribute("data-delete");
//var test2 = deletebutton.setAttribute("href", +test);
//
//console.log(test)
//console.log(test2)    
//}
