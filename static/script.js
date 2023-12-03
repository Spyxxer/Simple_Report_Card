var pageTitle = document.title;

if (pageTitle == 'Class Students'){
	console.log(true)
	const colors = ['red', 'orange', 'yellow', 'green', 'blue'];
	const buttons = document.querySelectorAll('.class-button');

	for(let classbutton of buttons){
		classbutton.addEventListener('click', function(event){
			var class_name = this.innerText;
			redirectURL = '/class/' + encodeURIComponent(class_name);
			window.location.href = redirectURL;
		});
	}

}


