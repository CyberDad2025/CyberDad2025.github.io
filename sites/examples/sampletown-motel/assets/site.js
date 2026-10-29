/* Client template JS: footer year, click-to-load map, quote form. Modes: "mailto" (default, $0) or "post"
   (only if the client approves a free form endpoint; set data-endpoint). Honeypot drops bot fills. No third-party scripts. */
(function(){
  document.querySelectorAll("[data-year]").forEach(function(n){n.textContent=new Date().getFullYear();});
  var m=document.querySelector(".map");
  if(m){ if(!m.dataset.mapSrc){m.remove();} else m.querySelector(".map-load").addEventListener("click",function(){
    var i=document.createElement("iframe"); i.src=m.dataset.mapSrc; i.title="Map"; i.loading="lazy"; i.width="600"; i.height="300";
    i.referrerPolicy="no-referrer-when-downgrade"; m.innerHTML=""; m.appendChild(i);});}
  var f=document.getElementById("contact-form"); if(!f) return;
  f.addEventListener("submit",function(e){
    e.preventDefault(); var st=f.querySelector(".form-status");
    if(f.website.value){st.textContent="Thanks.";return;}           /* honeypot: bots fill hidden field */
    var ph=f.phone.value.trim(), em=f.email.value.trim();
    if(!f.checkValidity()||(!ph&&!em)){var b=f.querySelector(":invalid")||f.phone; b.focus();
      st.textContent=(!ph&&!em)?"Please add a phone number or an email so we can reply.":"Please check the highlighted field."; return;}
    var d={name:f.name.value.trim(),phone:ph,email:em,service:f.service.value,zip:f.zip.value.trim(),message:f.message.value.trim()};
    if(f.dataset.mode==="post"&&f.dataset.endpoint){
      fetch(f.dataset.endpoint,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(d)})
        .then(function(r){st.textContent=r.ok?"Thanks, your request was sent.":"Sorry, that didn't work. Please call or email "+f.dataset.email+".";})
        .catch(function(){st.textContent="Sorry, that didn't work. Please call or email "+f.dataset.email+".";});
      return;
    }
    var body="Name: "+d.name+"\nPhone: "+d.phone+"\nEmail: "+d.email+"\nService: "+d.service+"\nZIP: "+d.zip+"\n\n"+d.message;
    location.href="mailto:"+f.dataset.email+"?subject="+encodeURIComponent((f.dataset.subject||"Website request")+" from "+d.name)+"&body="+encodeURIComponent(body);
    st.textContent="Your email app should open with your request. Press Send there. Nothing opened? Call us or email "+f.dataset.email+".";
  });
})();
