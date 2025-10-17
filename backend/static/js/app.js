(function(){
  const modeButtons = document.querySelectorAll("#modeButtons .btn");
  const panels = {
    camera: document.getElementById("cameraPanel"),
    file: document.getElementById("filePanel"),
    external: document.getElementById("externalPanel"),
  };
  const urlHash = new URL(window.location.href).hash.replace("#mode=","");
  let currentMode = urlHash || "camera";
  function showMode(m){
    currentMode = m;
    Object.values(panels).forEach(p=> p.classList.add("hidden"));
    panels[m].classList.remove("hidden");
  }
  modeButtons.forEach(btn => btn.addEventListener("click", ()=> showMode(btn.dataset.mode)));
  showMode(currentMode);

  // ===== Camera mode =====
  const video = document.getElementById("video");
  const canvas = document.getElementById("canvas");
  const ctx = canvas.getContext("2d");
  const btnOpenCam = document.getElementById("btnOpenCam");
  const btnSnap = document.getElementById("btnSnap");
  const btnRetry = document.getElementById("btnRetry");
  const btnConfirm = document.getElementById("btnConfirm");
  let stream = null;

  btnOpenCam.onclick = async ()=>{
    try{
      stream = await navigator.mediaDevices.getUserMedia({video:{facingMode:"environment"}, audio:false});
      video.srcObject = stream;
      await video.play();
      btnSnap.disabled = false;
    }catch(e){
      alert("เปิดกล้องไม่ได้: "+e.message);
    }
  };

  btnSnap.onclick = ()=>{
    if(!video.videoWidth) return;
    const scale = Math.min(canvas.width/video.videoWidth, canvas.height/video.videoHeight);
    const w = Math.round(video.videoWidth*scale), h = Math.round(video.videoHeight*scale);
    ctx.clearRect(0,0,canvas.width,canvas.height);
    ctx.drawImage(video, 0,0,w,h);
    btnConfirm.disabled = false;
    btnRetry.disabled = false;
  };

  btnRetry.onclick = ()=>{
    ctx.clearRect(0,0,canvas.width,canvas.height);
    btnConfirm.disabled = true;
    btnRetry.disabled = true;
  };

  btnConfirm.onclick = async ()=>{
    canvas.toBlob(async (blob)=>{
      const fd = new FormData();
      fd.append("file", blob, "capture.jpg");
      const r = await fetch("/api/upload", {method:"POST", body: fd});
      const js = await r.json();
      renderResult(js);
    }, "image/jpeg", 0.92);
  };

  // ===== File mode =====
  const fileInput = document.getElementById("fileInput");
  const fileCanvas = document.getElementById("fileCanvas");
  const fctx = fileCanvas.getContext("2d");
  const btnUpload = document.getElementById("btnUpload");

  fileInput.onchange = (ev)=>{
    const file = ev.target.files[0];
    if(!file) return;
    const img = new Image();
    img.onload = ()=>{
      const scale = Math.min(fileCanvas.width/img.width, fileCanvas.height/img.height);
      const w = Math.round(img.width*scale), h = Math.round(img.height*scale);
      fctx.clearRect(0,0,fileCanvas.width,fileCanvas.height);
      fctx.drawImage(img,0,0,w,h);
      btnUpload.disabled = false;
    };
    img.src = URL.createObjectURL(file);
  };

  btnUpload.onclick = async ()=>{
    const file = fileInput.files[0];
    if(!file) return;
    const fd = new FormData();
    fd.append("file", file);
    const r = await fetch("/api/upload", {method:"POST", body: fd});
    const js = await r.json();
    renderResult(js);
  };

  // ===== External mode =====
  const extUrl = document.getElementById("extUrl");
  const btnFetch = document.getElementById("btnFetch");
  const extCanvas = document.getElementById("extCanvas");
  const extCtx = extCanvas.getContext("2d");

  btnFetch.onclick = async ()=>{
    try{
      const r = await fetch(extUrl.value, {mode:"no-cors"});
      const blob = await r.blob();
      const img = new Image();
      img.onload = async ()=>{
        const scale = Math.min(extCanvas.width/img.width, extCanvas.height/img.height);
        const w = Math.round(img.width*scale), h = Math.round(img.height*scale);
        extCtx.clearRect(0,0,extCanvas.width,extCanvas.height);
        extCtx.drawImage(img,0,0,w,h);
        // send to backend for analysis
        extCanvas.toBlob(async (b)=>{
          const fd = new FormData();
          fd.append("file", b, "snapshot.jpg");
          const rr = await fetch("/api/upload", {method:"POST", body: fd});
          const js = await rr.json();
          renderResult(js);
        }, "image/jpeg", 0.92);
      };
      img.src = URL.createObjectURL(blob);
    }catch(e){
      alert("ดึงภาพไม่ได้: "+e.message);
    }
  };

  // ===== Render result & formula =====
  const resultPre = document.getElementById("resultPre");
  const formulaTbody = document.getElementById("formulaTbody");
  const btnMix = document.getElementById("btnMix");

  function renderResult(js){
    resultPre.textContent = JSON.stringify(js, null, 2);
    formulaTbody.innerHTML = "";
    if(js && js.formula_match){
      const f = js.formula_match;
      const rows = [
        ["Red", f.base_red],
        ["Blue", f.base_blue],
        ["Yellow", f.base_yellow],
        ["White", f.base_white],
        ["Black", f.base_black],
      ];
      rows.forEach(([name, val])=>{
        const tr = document.createElement("tr");
        tr.innerHTML = `<td>${name}</td><td>${val.toFixed(2)}%</td>`;
        formulaTbody.appendChild(tr);
      });
    }
  }

  btnMix.onclick = async ()=>{
    // In real usage set ENV ESP32_URL to http://<ip>:<port>
    // Here we just forward the current formula to backend
    const rows = [...formulaTbody.querySelectorAll("tr")];
    if(!rows.length){ alert("ไม่มีสูตรสี"); return; }
    const payload = {};
    rows.forEach(tr => {
      const base = tr.children[0].textContent.toLowerCase();
      const val = parseFloat(tr.children[1].textContent.replace("%",""));
      payload[base] = val;
    });
    const r = await fetch("/api/mix", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify(payload)});
    const js = await r.json();
    alert("คำสั่งผสมสี: " + JSON.stringify(js));
  };

})();