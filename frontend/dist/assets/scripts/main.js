console.log("'Allo 'Allo!");var force=!1;$(".mobile-toggle__bd").click(function(a){a.preventDefault(),$(".navbar").slideToggle(200),force?$(".navbar").addClass("navbar--forced"):$(".navbar").removeClass("navbar--forced"),force=!force});