window.parseISOString = function parseISOString(s) {
  var b = s.split(/\D+/);
  return new Date(Date.UTC(b[0], --b[1], b[2], b[3], b[4], b[5], b[6]));
};

if(window.location.pathname.substr(0, 8) == '/venues/' && window.location.pathname.substr(7,8) != '/create')
	{
		//sends delete request to the server
		document.getElementById('deleteBtn').addEventListener('click', function(e) {
			e.preventDefault();
			let numVenue = e.target.dataset.id;

			fetch(`/venues/${numVenue}`, {
				method: 'DELETE'
			});
		});
	}
