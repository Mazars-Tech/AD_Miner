function display_one_hexagon(name, hexa_dict) {
  var color = hexa_dict.color;
  var x = hexa_dict.position[0];
  var y = hexa_dict.position[1];
  var link = hexa_dict.link;

  switch (color) {
    case 'red':
      var status =
        "<i class='bi bi-exclamation-diamond-fill' style='color: rgb(245, 75, 75); margin-right: 3px;'></i> Immediate risk";
      break;
    case 'orange':
      var status =
        "<i class='bi bi-exclamation-triangle-fill' style='color: rgb(245, 177, 75); margin-right: 3px;'></i> Potential risk";
      break;
    case 'yellow':
      var status =
        "<i class='bi bi-dash-circle-fill' style='color: rgb(255, 221, 0); margin-right: 3px;'></i> Minor risk";
      break;
    case 'green':
      var status =
        "<i class='bi bi-check-circle-fill' style='color: rgb(91, 180, 32); margin-right: 3px;'></i> Handled risk";
      break;
    default:
      var status =
        "<i class='bi bi-dash-circle-fill' style='color: rgb(133,135,150); margin-right: 3px;'></i> Risk not evaluated";
  }

  var style = `top: ${x}%; left: ${y}%`;

  var hexagon = `<a href="${link}">
        <img src="../icons/main_circle/hexagone_${color}.svg" class="hexagon hexagon-${color}" style="${style}" custom-title="${hexa_dict.title}" custom-status="${status}"/>
    </a>`;

  $('.main_circle').append(hexagon);
}

function display_all_hexagons(dico_entry) {
  // Display all icons
  for (var key in dico_entry) {
    display_one_hexagon(key, dico_entry[key]);
  }

  // Create main text
  var hexa_display = `
    <div id="hexa-main-div">
        <h5>HEXA NAME</h5>
        <br/>
        <p>STATUS</p>
    </div>`;
  $('.main_circle').append(hexa_display);

  // Add event listener on hover for hexagons to display the main text

  const hexagons = document.querySelectorAll('.hexagon');

  hexagons.forEach((el) =>
    el.addEventListener('mouseover', (event) => {
      var div = document.querySelector('#hexa-main-div');
      div.querySelector('h5').innerText = el.getAttribute('custom-title');
      div.querySelector('p').innerHTML = el.getAttribute('custom-status');
      div.style.opacity = 1;
    }),
  );

  const card_right = document.querySelectorAll('.threat-card');

  card_right.forEach((el) =>
    el.addEventListener('mouseover', (event) => {
      var div = document.querySelector('#hexa-main-div');
      div.querySelector('h5').innerText = el.getAttribute('custom-title');
      div.querySelector('p').innerHTML = el.getAttribute('custom-status');
      div.style.opacity = 1;
    }),
  );

  card_right.forEach((el) =>
    el.addEventListener('mouseleave', (event) => {
      var div = document.querySelector('#hexa-main-div');
      div.style.opacity = 0;
    }),
  );

  hexagons.forEach((el) =>
    el.addEventListener('mouseleave', (event) => {
      var div = document.querySelector('#hexa-main-div');
      div.style.opacity = 0;
    }),
  );

  var title_permissions = `<a data-bs-toggle="modal" href="#cardsModal" onclick=switchCards('permission')>
    <img src="../icons/main_circle/permissions.svg" class="title-section shadow" style="top:15%; left: 40%""/>
    </a>`;
  $('.main_circle').append(title_permissions);

  var title_passwords = `<a data-bs-toggle="modal" href="#cardsModal" onclick=switchCards('passwords')>
        <img src="../icons/main_circle/passwords.svg" class="title-section shadow" style="top:62%; left: 10%""/>
    </a>`;
  $('.main_circle').append(title_passwords);

  var title_kerberos = `<a data-bs-toggle="modal" href="#cardsModal" onclick=switchCards('kerberos')>
        <img src="../icons/main_circle/kerberos.svg" class="title-section shadow" style="top:62%; left: 70%;""/>
    </a>`;
  $('.main_circle').append(title_kerberos);


  var title_misc = `<a data-bs-toggle="modal" href="#cardsModal" onclick=switchCards('misc')>
        <img src="../icons/main_circle/misc.svg" class="title-section shadow" style="top:80%; left: 45%;""/>
    </a>`;
  $('.main_circle').append(title_misc);

}
