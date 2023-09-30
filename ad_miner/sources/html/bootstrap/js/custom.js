var description_info = document.getElementById('description_info').textContent;
var description_risk = document.getElementById('description_risk').textContent;
var description_poa = document.getElementById('description_poa').textContent;

if (description_info != '' || description_risk != '' || description_poa != '') {
  document.getElementById('button_description').style.display = 'inline';
}

if (description_info != '') {
  document.getElementById('description_part').style.visibility = 'visible';
}

if (description_risk != '') {
  document.getElementById('risk_part').style.visibility = 'visible';
}

if (description_poa != '') {
  document.getElementById('poa_part').style.visibility = 'visible';
}

// var text_current_page_title = document.getElementById('title_page_h4').textContent;

// document.getElementById('title_current_page').textContent = text_current_page_title;

var graph_presence = document.getElementById('switch_hide_node');

if (graph_presence != null) {
  document.getElementById('button_parameter').style.display = 'inline';
}

if (graph_presence != null) {
  document.getElementById('search-bar-list-group').style.display = 'inline';
}

if (graph_presence != null) {
  document.getElementById('button_path').style.display = 'inline';
}


var grid_presence = document.getElementById('myGrid');

if (grid_presence != null) {
  document.getElementById('button_download').style.display = 'inline';
}

window.addEventListener('click', function (e) {
  if (!document.getElementById('collapseSettings').contains(e.target)) {
    $('.collapse').collapse('hide');
  }
});
