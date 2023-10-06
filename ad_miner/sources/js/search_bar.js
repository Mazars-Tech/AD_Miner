/*
Controls the search bar on the main page.
*/

// Hide and display the search bar
function toggleSearch() {
    const searchBarDiv = document.getElementById("search-bar-div");
    //searchBarDiv.style.display = (searchBarDiv.style.display === "block") ? "none" : "block";
    (searchBarDiv.classList.contains("search-bar-div-show")) ? searchBarDiv.classList.remove("search-bar-div-show") : searchBarDiv.classList.add("search-bar-div-show");
    searchBar.focus();
}

const searchBar = document.getElementById("search-bar");
const controlDropdown = document.getElementById("search-dropdown");

// Event listener for input in the search bar
searchBar.addEventListener("input", function() {
    const searchTerm = searchBar.value.toLowerCase().trim();
    
    if (searchTerm === "") {
        // If the input is empty, hide the dropdown
        controlDropdown.classList.remove("active");
    } else {
        // Filter controls by name and description
        const filteredControls = Object.values(dico_entry).filter(control => control.name.toLowerCase().includes(searchTerm) || control.title.toLowerCase().includes(searchTerm));
        updateDropdown(filteredControls);
    }
});

// Function to update the dropdown with filtered controls
function updateDropdown(filteredControls) {
    controlDropdown.innerHTML = "";
    const icon_search = {
        "red": '<i class="bi bi-exclamation-diamond-fill search-element-icon" style="color: rgb(245, 75, 75);"></i>',
        "orange": '<i class="bi bi-exclamation-triangle-fill search-element-icon" style="color: rgb(245, 177, 75);"></i>',
        "yellow": '<i class="bi bi-dash-circle-fill search-element-icon" style="color: rgb(255, 221, 0);"></i>',
        "green": '<i class="bi bi-check-circle-fill search-element-icon" style="color: rgb(91, 180, 32);"></i>'
    };
    filteredControls.forEach(control => {
        const dropdownItem = document.createElement("a");
        dropdownItem.classList.add("dropdown-item");
        dropdownItem.href = control.link;

        // Highlight search input in result
        const searchTerm = searchBar.value.toLowerCase().trim();
        var regex = new RegExp(searchTerm, 'gi');
        var name = control.name.replace(regex, '<span class="search-highlight">$&</span>');
        var title = control.title.replace(regex, '<span class="search-highlight">$&</span>');

        "aa".replace()
        dropdownItem.innerHTML = `
        <div class="container">
            <div class="row">
                <div class="col-1 search-element-icon-div">
                    ${icon_search[control.color]}
                </div>
                <div class="col-11">
                    <p class="search-element-name">
                        ${name}
                    </p>
                    <p class="search-element-description">
                        ${title}
                    </p>
                </div>
            </div>
        </div>
        `;
        // Add link to dropdown item
        dropdownItem.addEventListener("click", function() {
            searchBar.value = "";
        });
        controlDropdown.appendChild(dropdownItem);
    });

    if (filteredControls.length > 0) {
        controlDropdown.classList.add("active");
    } else {
        controlDropdown.classList.remove("active");
    }
}