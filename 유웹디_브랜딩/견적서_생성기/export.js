/* 견적서 HTML → PDF(A4, 2페이지) + PPTX(A4, 편집 가능) 내보내기
 * 사용법: node export.js <견적서.html> [출력파일_기본이름]
 * 환경변수: CHROME_PATH (크롬 실행 파일 경로, 선택)
 */
const path = require('path');
const { chromium } = require('playwright');
const pptxgen = require('pptxgenjs');
const HTMLFILE = path.resolve(process.argv[2] || '');
if (!process.argv[2]) { console.error('사용법: node export.js 견적서.html [출력이름]'); process.exit(1); }
const BASE = path.resolve(process.argv[3] || HTMLFILE.replace(/\.html$/, ''));
const HTML = 'file://' + encodeURI(HTMLFILE);

function extract(){
  const pages=[...document.querySelectorAll('.page')];
  const P=(c)=>{const m=c.match(/rgba?\(([^)]+)\)/); if(!m) return {r:0,g:0,b:0,a:0}; const v=m[1].split(',').map(s=>parseFloat(s)); return {r:v[0],g:v[1],b:v[2],a:v.length>3?v[3]:1};};
  const hex=(o)=>[o.r,o.g,o.b].map(n=>Math.round(n).toString(16).padStart(2,'0')).join('').toUpperCase();
  const num=(s)=>parseFloat(s)||0;
  const bgBehind=(el)=>{let e=el.parentElement; while(e){const c=P(getComputedStyle(e).backgroundColor); if(c.a>0.9) return c; e=e.parentElement;} return {r:255,g:255,b:255,a:1};};
  const opacityOf=(el)=>{let o=1,e=el; while(e){o*=parseFloat(getComputedStyle(e).opacity); e=e.parentElement;} return o;};
  return pages.map(page=>{
    const pr=page.getBoundingClientRect(); const out=[];
    const rel=(r)=>({x:r.left-pr.left,y:r.top-pr.top,w:r.width,h:r.height});
    function textPrims(node, el, cs){
      const raw=node.nodeValue; const t=raw.trim(); if(!t) return;
      const s=raw.indexOf(t[0]); const e0=s+t.length;
      const rg=document.createRange();
      // 줄 단위 분리 (글자별 위치로 줄바꿈 판단)
      const lines=[]; let cur=null;
      for(let i=s;i<e0;i++){
        rg.setStart(node,i); rg.setEnd(node,i+1); const rs=rg.getClientRects(); if(!rs.length) continue; const r=rs[0];
        if(raw[i]===' '&&!cur) continue;
        if(!cur||Math.abs(r.top-cur.top)>4){cur={top:r.top,left:r.left,right:r.right,bottom:r.bottom,text:''};lines.push(cur);}
        cur.text+=raw[i]; cur.right=Math.max(cur.right,r.right); cur.left=Math.min(cur.left,r.left); cur.bottom=Math.max(cur.bottom,r.bottom);
      }
      const fs=num(cs.fontSize); const wt=parseInt(cs.fontWeight);
      const al=cs.textAlign; const par=el.parentElement; const pcs=par?getComputedStyle(par):null;
      const hasElKids=[...el.children].some(k=>k.textContent.trim());
      const rightAnchor=(al==='right'||al==='end')||(pcs&&pcs.display==='flex'&&pcs.justifyContent==='space-between'&&!el.nextElementSibling&&el!==par.firstElementChild&&!hasElKids);
      const op=opacityOf(el); const col=P(cs.color); const bb=bgBehind(el);
      const a=col.a*op; const eff={r:col.r*a+bb.r*(1-a),g:col.g*a+bb.g*(1-a),b:col.b*a+bb.b*(1-a)};
      const ls=cs.letterSpacing==='normal'?0:num(cs.letterSpacing);
      lines.forEach(L=>{
        const w=(L.right-L.left); const slack=w*0.04+4; const W=w+slack;
        const x=rightAnchor? (L.right-pr.left)-W : (L.left-pr.left);
        out.push({k:'text',text:L.text,x,y:L.top-pr.top,w:W,h:L.bottom-L.top,fs,wt,color:hex(eff),align:rightAnchor?'right':'left',ls});
      });
    }
    function walk(el){
      const cs=getComputedStyle(el); if(cs.display==='none') return;
      const r=rel(el.getBoundingClientRect());
      if(el!==page){
        if(el.tagName==='IMG'){ out.push({k:'img',...r,src:el.src}); return; }
        if(el.tagName==='INPUT'){ out.push({k:'check',...r}); return; }
        const bg=P(cs.backgroundColor);
        const bw=['Top','Right','Bottom','Left'].map(s=>cs['border'+s+'Style']==='none'?0:num(cs['border'+s+'Width']));
        const bc=['Top','Right','Bottom','Left'].map(s=>hex(P(cs['border'+s+'Color'])));
        const rad=['TopLeft','TopRight','BottomRight','BottomLeft'].map(s=>num(cs['border'+s+'Radius']));
        let topRound=0;
        const par=el.parentElement; const pcs=par?getComputedStyle(par):null;
        if(rad[0]>0&&rad[1]>0&&rad[2]===0&&rad[3]===0) topRound=Math.min(rad[0],r.h/2);
        else if(pcs&&pcs.overflow!=='visible'&&num(pcs.borderTopLeftRadius)>0&&bg.a>0&&rad.every(v=>v===0)&&Math.abs(el.getBoundingClientRect().top-(par.getBoundingClientRect().top+num(pcs.borderTopWidth)))<1.5) topRound=num(pcs.borderTopLeftRadius)-1;
        const uni=bw.every(v=>v===bw[0])&&bc.every(v=>v===bc[0])&&bw[0]>0;
        const radius=rad.every(v=>v===rad[0])?Math.min(rad[0],Math.min(r.w,r.h)/2):0;
        if(bg.a>0.01||uni){
          out.push({k:'box',...r,fill:bg.a>0.01?hex(bg):null,line:uni?bc[0]:null,lw:uni?bw[0]:0,radius,topRound});
        }
        if(!uni){
          if(bw[0]) out.push({k:'line',x1:r.x,y1:r.y+bw[0]/2,x2:r.x+r.w,y2:r.y+bw[0]/2,color:bc[0],lw:bw[0]});
          if(bw[2]) out.push({k:'line',x1:r.x,y1:r.y+r.h-bw[2]/2,x2:r.x+r.w,y2:r.y+r.h-bw[2]/2,color:bc[2],lw:bw[2]});
          if(bw[1]) out.push({k:'line',x1:r.x+r.w-bw[1]/2,y1:r.y,x2:r.x+r.w-bw[1]/2,y2:r.y+r.h,color:bc[1],lw:bw[1]});
          if(bw[3]) out.push({k:'line',x1:r.x+bw[3]/2,y1:r.y,x2:r.x+bw[3]/2,y2:r.y+r.h,color:bc[3],lw:bw[3]});
        }
        if(cs.display==='list-item'){
          // 불릿: 첫 줄 중앙
          const rg=document.createRange(); const tn=[...el.childNodes].find(n=>n.nodeType===3&&n.nodeValue.trim());
          if(tn){ rg.selectNodeContents(tn); const f=rg.getClientRects()[0]; const col=hex(P(cs.color));
            out.push({k:'dot',x:el.getBoundingClientRect().left-pr.left-11.5,y:(f.top+f.bottom)/2-pr.top,d:4.5,color:col}); }
        }
      }
      el.childNodes.forEach(n=>{ if(n.nodeType===1) walk(n); else if(n.nodeType===3) textPrims(n,el,cs); });
    }
    walk(page);
    return {w:pr.width,h:pr.height,items:out};
  });
}

(async()=>{
  const b=await chromium.launch({executablePath:process.env.CHROME_PATH||undefined,args:['--no-sandbox']});
  const p=await b.newPage({viewport:{width:1000,height:1300}});
  await p.emulateMedia({media:'print'});
  await p.setViewportSize({width:794,height:1123});
  await p.goto(HTML); await p.evaluate(()=>document.fonts.ready);
  const pages=await p.evaluate(extract);
  // 페이지 넘침 검사
  const fit=await p.evaluate(()=>[...document.querySelectorAll('.page')].map(pg=>{
    const kids=[...pg.children].filter(e=>!e.classList.contains('pgfoot')&&!e.classList.contains('sample'));
    const last=kids[kids.length-1].getBoundingClientRect(), r=pg.getBoundingClientRect();
    return {bottom:last.bottom-r.top, foot:pg.querySelector('.pgfoot').getBoundingClientRect().top-r.top};
  }));
  const over=fit.map((f,i)=>f.bottom>f.foot-4?`${i+1}페이지`:null).filter(Boolean);
  if(over.length){ console.error('경고: 내용이 푸터를 침범합니다 → '+over.join(', ')+' (항목 수·문구를 줄여 주세요)'); process.exitCode=2; }
  await p.emulateMedia({media:'print'});
  await p.pdf({path:BASE+'.pdf',format:'A4',printBackground:true,preferCSSPageSize:true});
  await b.close();

  const pres=new pptxgen();
  pres.defineLayout({name:'A4',width:8.2677,height:11.6929}); pres.layout='A4';
  pres.title=path.basename(BASE); pres.author='유웹디';
  const I=(v)=>v/96, PT=(v)=>v*0.75;
  const mergeLines=(items)=>{
    const res=[]; 
    items.forEach(it=>{
      if(it.k==='line'&&Math.abs(it.y1-it.y2)<0.01){
        const prev=res.find(r=>r.k==='line'&&Math.abs(r.y1-r.y2)<0.01&&Math.abs(r.y1-it.y1)<0.6&&r.color===it.color&&r.lw===it.lw&&Math.abs(r.x2-it.x1)<1.5);
        if(prev){res.splice(res.indexOf(prev),1); prev.x2=it.x2; res.push(prev); return;}
      }
      res.push(it);
    });
    return res;
  };
  pages.forEach((pg,pi)=>{
    pg.items=mergeLines(pg.items);
    const s=pres.addSlide(); s.background={color:'FFFFFF'};
    let n=0;
    pg.items.forEach(it=>{
      const name=`${it.k}-${++n}`;
      if(it.k==='box'){
        const o={x:I(it.x),y:I(it.y),w:I(it.w),h:I(it.h),objectName:name};
        o.fill=it.fill?{color:it.fill}:{type:'none'};
        o.line=it.line?{color:it.line,width:PT(it.lw)}:{type:'none'};
        let shape=pres.ShapeType.rect;
        if(it.topRound){shape=pres.ShapeType.round2SameRect;}
        else if(it.radius>0){shape=pres.ShapeType.roundRect; o.rectRadius=I(it.radius);}
        s.addShape(shape,o);
      } else if(it.k==='line'){
        s.addShape(pres.ShapeType.line,{x:I(it.x1),y:I(it.y1),w:I(it.x2-it.x1),h:I(it.y2-it.y1),line:{color:it.color,width:PT(it.lw)},objectName:name});
      } else if(it.k==='img'){
        s.addImage({data:it.src.replace(/^data:/,''),x:I(it.x),y:I(it.y),w:I(it.w),h:I(it.h),altText:'유웹디 로고',objectName:name});
      } else if(it.k==='check'){
        s.addShape(pres.ShapeType.roundRect,{x:I(it.x),y:I(it.y),w:I(it.w),h:I(it.h),rectRadius:I(2.5),fill:{color:'FFFFFF'},line:{color:'767676',width:1.25},objectName:name});
      } else if(it.k==='dot'){
        s.addShape(pres.ShapeType.ellipse,{x:I(it.x-it.d/2),y:I(it.y-it.d/2),w:I(it.d),h:I(it.d),fill:{color:it.color},line:{type:'none'},objectName:name});
      } else if(it.k==='text'){
        const face=it.wt>=700?'Pretendard':(it.wt>=600?'Pretendard SemiBold':'Pretendard');
        const o={x:I(it.x),y:I(it.y),w:I(it.w),h:I(it.h),fontFace:face,fontSize:PT(it.fs),color:it.color,bold:it.wt>=700,
          align:it.align,valign:'middle',margin:0,wrap:false,isTextBox:true,lang:'ko-KR',objectName:name};
        if(it.ls) o.charSpacing=PT(it.ls);
        s.addText(it.text,o);
      }
    });
  });
  await pres.writeFile({fileName:BASE+'_A4.pptx'});
  console.log('PDF :',BASE+'.pdf');
  console.log('PPTX:',BASE+'_A4.pptx');
})();
