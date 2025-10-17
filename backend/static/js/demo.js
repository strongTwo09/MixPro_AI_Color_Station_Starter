
    // ===== Utilities สี =====
    const clamp = (x, a=0, b=1) => Math.min(b, Math.max(a, x));
    const hexToRgb = (hex) => {
      const s = hex.replace('#','').trim();
      const v = s.length === 3 ? s.split('').map(c=>c+c).join('') : s;
      const n = parseInt(v, 16);
      return [ (n>>16)&255, (n>>8)&255, n&255 ];
    };
    const rgbToHex = ([r,g,b]) => '#'+[r,g,b].map(v=>v.toString(16).padStart(2,'0')).join('');
    const srgbToLinear = (c)=>{
      c/=255; return c<=0.04045? c/12.92 : Math.pow((c+0.055)/1.055, 2.4);
    };
    const linearToSrgb = (c)=>{
      const v = c<=0.0031308? 12.92*c : 1.055*Math.pow(c,1/2.4)-0.055;
      return Math.round(clamp(v,0,1)*255);
    };
    const rgbToLinear = (rgb)=> rgb.map(srgbToLinear);
    const linearToRgb = (lin)=> lin.map(linearToSrgb);
    function deltaRGB(a,b){ return Math.sqrt((a[0]-b[0])**2+(a[1]-b[1])**2+(a[2]-b[2])**2).toFixed(2); }

    // ===== Preset โทนเนอร์ตามยี่ห้อ (เดโม) =====
    const BRAND_PRESETS = {
      TOY: [
        {name:'TO-W1 (ขาว)', hex:'#ffffff'},
        {name:'TO-BK (ดำ)', hex:'#000000'},
        {name:'TO-R1', hex:'#c62828'},
        {name:'TO-Y1', hex:'#fdd835'},
        {name:'TO-B1', hex:'#1e88e5'},
        {name:'TO-G1', hex:'#2e7d32'},
      ],
      HON: [
        {name:'HN-WH', hex:'#ffffff'},
        {name:'HN-BK', hex:'#000000'},
        {name:'HN-R', hex:'#cc3333'},
        {name:'HN-Y', hex:'#ffd54f'},
        {name:'HN-B', hex:'#1976d2'},
        {name:'HN-G', hex:'#388e3c'},
      ],
      ISZ: [
        {name:'IZ-W', hex:'#ffffff'},
        {name:'IZ-K', hex:'#000000'},
        {name:'IZ-R', hex:'#b71c1c'},
        {name:'IZ-Y', hex:'#ffeb3b'},
        {name:'IZ-B', hex:'#2196f3'},
        {name:'IZ-G', hex:'#2e7d32'},
      ],
      MAZ: [
        {name:'MZ-W', hex:'#ffffff'},
        {name:'MZ-K', hex:'#000000'},
        {name:'MZ-R', hex:'#d32f2f'},
        {name:'MZ-Y', hex:'#fbc02d'},
        {name:'MZ-B', hex:'#1e88e5'},
        {name:'MZ-G', hex:'#2e7d32'},
      ],
      MIT: [
        {name:'MT-W', hex:'#ffffff'},
        {name:'MT-K', hex:'#000000'},
        {name:'MT-R', hex:'#c62828'},
        {name:'MT-Y', hex:'#fdd835'},
        {name:'MT-B', hex:'#1976d2'},
        {name:'MT-G', hex:'#388e3c'},
      ],
      NIS: [
        {name:'NS-W', hex:'#ffffff'},
        {name:'NS-K', hex:'#000000'},
        {name:'NS-R', hex:'#c62828'},
        {name:'NS-Y', hex:'#fbc02d'},
        {name:'NS-B', hex:'#1e88e5'},
        {name:'NS-G', hex:'#2e7d32'},
      ],
      FOR: [
        {name:'FD-W', hex:'#ffffff'},
        {name:'FD-K', hex:'#000000'},
        {name:'FD-R', hex:'#c62828'},
        {name:'FD-Y', hex:'#fdd835'},
        {name:'FD-B', hex:'#1976d2'},
        {name:'FD-G', hex:'#2e7d32'},
      ],
      BMW: [
        {name:'BM-W', hex:'#ffffff'},
        {name:'BM-K', hex:'#000000'},
        {name:'BM-R', hex:'#b71c1c'},
        {name:'BM-Y', hex:'#ffeb3b'},
        {name:'BM-B', hex:'#1565c0'},
        {name:'BM-G', hex:'#2e7d32'},
      ],
      MBZ: [
        {name:'MB-W', hex:'#ffffff'},
        {name:'MB-K', hex:'#000000'},
        {name:'MB-R', hex:'#c62828'},
        {name:'MB-Y', hex:'#ffd54f'},
        {name:'MB-B', hex:'#1e88e5'},
        {name:'MB-G', hex:'#2e7d32'},
      ],
      HYU: [
        {name:'HY-W', hex:'#ffffff'},
        {name:'HY-K', hex:'#000000'},
        {name:'HY-R', hex:'#c62828'},
        {name:'HY-Y', hex:'#fdd835'},
        {name:'HY-B', hex:'#1e88e5'},
        {name:'HY-G', hex:'#2e7d32'},
      ],
      KIA: [
        {name:'KI-W', hex:'#ffffff'},
        {name:'KI-K', hex:'#000000'},
        {name:'KI-R', hex:'#c62828'},
        {name:'KI-Y', hex:'#ffd54f'},
        {name:'KI-B', hex:'#1976d2'},
        {name:'KI-G', hex:'#388e3c'},
      ],
      MG: [
        {name:'MG-W', hex:'#ffffff'},
        {name:'MG-K', hex:'#000000'},
        {name:'MG-R', hex:'#c62828'},
        {name:'MG-Y', hex:'#fdd835'},
        {name:'MG-B', hex:'#1e88e5'},
        {name:'MG-G', hex:'#2e7d32'},
      ]
    };

    let currentBrand = 'TOY';
    let baseColors = JSON.parse(JSON.stringify(BRAND_PRESETS[currentBrand]));

    // Render UI ของฐานสี
    const basesDiv = document.getElementById('bases');
    function renderBases(){
      basesDiv.innerHTML = '';
      baseColors.forEach((b,i)=>{
        const row = document.createElement('div');
        row.className = 'row';
        row.style.marginBottom = '8px';
        row.innerHTML = `
          <span class="swatch" style="background:${b.hex}"></span>
          <input type="text" value="${b.name}" style="width:200px"> 
          <input type="text" value="${b.hex}" style="width:110px">
          <button class="btn">ลบ</button>
        `;
        const [nameInp, hexInp, delBtn] = row.querySelectorAll('input,button');
        nameInp.addEventListener('input', ()=>{ b.name = nameInp.value; });
        hexInp.addEventListener('input', ()=>{ b.hex = hexInp.value; row.querySelector('.swatch').style.background = b.hex; });
        delBtn.addEventListener('click', ()=>{ baseColors.splice(i,1); renderBases(); });
        basesDiv.appendChild(row);
      });
    }
    renderBases();

    document.getElementById('addBase').onclick = ()=>{
      baseColors.push({name:`${currentBrand}-NEW`, hex:'#888888'});
      renderBases();
    };

    // ===== กล้อง/ภาพต้นฉบับ =====
    const video = document.getElementById('video');
    const canvasSrc = document.getElementById('canvasSrc');
    const ctxSrc = canvasSrc.getContext('2d');
    const fileInp = document.getElementById('file');
    const openCamBtn = document.getElementById('openCam');
    const snapBtn = document.getElementById('snap');

    fileInp.addEventListener('change', (e)=>{
      const file = e.target.files[0];
      if(!file) return;
      const img = new Image();
      img.onload = ()=>{
        const scale = Math.min(canvasSrc.width/img.width, canvasSrc.height/img.height);
        const w = Math.round(img.width*scale), h = Math.round(img.height*scale);
        ctxSrc.clearRect(0,0,canvasSrc.width,canvasSrc.height);
        ctxSrc.drawImage(img, 0,0, w,h);
      };
      img.src = URL.createObjectURL(file);
      stopCamera();
    });

    let stream = null;
    async function startCamera(){
      try {
        stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' }, audio: false });
        video.srcObject = stream;
        video.style.display = 'block';
        await video.play();
        snapBtn.disabled = false;
      } catch(err){
        alert('ไม่สามารถเปิดกล้องได้: '+err.message);
      }
    }
    function stopCamera(){
      if(stream){ stream.getTracks().forEach(t=>t.stop()); stream=null; }
      video.pause();
      video.style.display = 'none';
      snapBtn.disabled = true;
    }
    openCamBtn.onclick = ()=>{ startCamera(); };

    snapBtn.onclick = ()=>{
      if(!video.videoWidth) return;
      const scale = Math.min(canvasSrc.width/video.videoWidth, canvasSrc.height/video.videoHeight);
      const w = Math.round(video.videoWidth*scale), h = Math.round(video.videoHeight*scale);
      ctxSrc.clearRect(0,0,canvasSrc.width,canvasSrc.height);
      ctxSrc.drawImage(video, 0,0, w,h);
    };

    const eyedropBtn = document.getElementById('eyedrop');
    const pickedInfo = document.getElementById('pickedInfo');
    eyedropBtn.onclick = ()=>{
      canvasSrc.style.cursor = 'crosshair';
      const onPick = (ev)=>{
        const rect = canvasSrc.getBoundingClientRect();
        const x = Math.floor((ev.clientX-rect.left)*canvasSrc.width/rect.width);
        const y = Math.floor((ev.clientY-rect.top)*canvasSrc.height/rect.height);
        const d = ctxSrc.getImageData(x,y,1,1).data; // RGBA
        const hex = rgbToHex([d[0],d[1],d[2]]);
        targetHex.value = hex; targetSw.style.background = hex;
        pickedInfo.textContent = `RGB(${d[0]},${d[1]},${d[2]}) ${hex}`;
        canvasSrc.style.cursor = 'default';
        canvasSrc.removeEventListener('click', onPick);
      };
      canvasSrc.addEventListener('click', onPick);
    };

    // ===== Solver (Projected Gradient Descent แบบง่าย) =====
    function solveMixtureRGB(targetHex, bases){
      const tRGB = hexToRgb(targetHex);
      const tLin = rgbToLinear(tRGB);
      const A = bases.map(b=> rgbToLinear(hexToRgb(b.hex)) ); // m x 3
      const m = A.length;
      let w = new Array(m).fill(1/m); // เริ่มต้นเท่ากัน
      const alpha = 0.05; // อัตราเรียนรู้
      for(let iter=0; iter<800; iter++){
        // y = A^T w  (3 ช่อง)
        let y = [0,0,0];
        for(let i=0;i<m;i++){
          y[0]+=w[i]*A[i][0]; y[1]+=w[i]*A[i][1]; y[2]+=w[i]*A[i][2];
        }
        const grad = new Array(m).fill(0);
        for(let i=0;i<m;i++){
          grad[i] = (y[0]-tLin[0])*A[i][0] + (y[1]-tLin[1])*A[i][1] + (y[2]-tLin[2])*A[i][2];
        }
        for(let i=0;i<m;i++){ w[i] = Math.max(0, w[i] - alpha*grad[i]); }
        let s = w.reduce((a,b)=>a+b,0); if(s===0){ w.fill(1/m); } else { for(let i=0;i<m;i++) w[i]/=s; }
      }
      let mixLin = [0,0,0];
      for(let i=0;i<m;i++){
        mixLin[0]+=w[i]*A[i][0]; mixLin[1]+=w[i]*A[i][1]; mixLin[2]+=w[i]*A[i][2];
      }
      const mixRGB = linearToRgb(mixLin);
      return {weights:w, mixRGB, targetRGB:tRGB};
    }

    // ===== Hook UI คำนวณ =====
    const targetHex = document.getElementById('targetHex');
    const targetSw = document.getElementById('targetSw');
    targetHex.addEventListener('input', ()=>{ targetSw.style.background = targetHex.value; });

    const solveBtn = document.getElementById('solve');
    const tblBody = document.querySelector('#resultTbl tbody');
    const mixSw = document.getElementById('mixSw');
    const mixHexEl = document.getElementById('mixHex');
    const mixDelta = document.getElementById('mixDelta');
    const deltaEl = document.getElementById('delta');
    const brandSel = document.getElementById('brand');
    const brandInfo = document.getElementById('brandInfo');

    brandSel.addEventListener('change', ()=>{
      currentBrand = brandSel.value;
      baseColors = JSON.parse(JSON.stringify(BRAND_PRESETS[currentBrand]));
      brandInfo.textContent = `BRAND: ${currentBrand}`;
      renderBases();
    });

    solveBtn.onclick = ()=>{
      try{
        const res = solveMixtureRGB(targetHex.value, baseColors);
        const batch = parseFloat(document.getElementById('batch').value||'500');
        const step = parseFloat(document.getElementById('minStep').value||'0.1');
        const perc = res.weights.map(w=> w*100);
        let grams = perc.map(p=> p/100*batch);
        grams = grams.map(g=> Math.round(g/step)*step);
        let total = grams.reduce((a,b)=>a+b,0);
        if(total<=0) total=1;
        grams = grams.map(g=> g*batch/total);

        tblBody.innerHTML = '';
        baseColors.forEach((b,i)=>{
          if(grams[i] <= 0) return;
          const tr = document.createElement('tr');
          tr.innerHTML = `
            <td><span class="swatch" style="background:${b.hex}"></span>${b.name}</td>
            <td><code>${b.hex}</code></td>
            <td>${(perc[i]).toFixed(2)}%</td>
            <td>${grams[i].toFixed(2)}</td>
          `;
          tblBody.appendChild(tr);
        });

        const mixHex = rgbToHex(res.mixRGB);
        mixSw.style.background = mixHex;
        mixHexEl.textContent = mixHex;
        mixDelta.textContent = `ΔRGB: ${deltaRGB(res.mixRGB, res.targetRGB)}`;
        deltaEl.textContent = `เป้าหมาย: ${targetHex.value.toUpperCase()} → คำนวณแล้ว: ${mixHex.toUpperCase()} | ΔRGB: ${deltaRGB(res.mixRGB, res.targetRGB)}`;
      }catch(e){
        alert('คำนวณไม่สำเร็จ: '+e.message);
      }
    };
