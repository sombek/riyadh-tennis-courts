'use strict';
const icons = {
  ball:'<circle cx="12" cy="12" r="9"/><path d="M5 5c5 2 9 6 14 14M5 19c2-5 6-9 14-14"/>',
  court:'<rect x="3" y="4" width="18" height="16" rx="1"/><path d="M6 4v16M18 4v16M3 12h18M6 8h12M6 16h12M12 8v8"/>',
  pin:'<path d="M20 10c0 6-8 11-8 11S4 16 4 10a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10" r="2.5"/>',
  search:'<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/>',
  bookmark:'<path d="M6 4h12v17l-6-4-6 4V4Z"/>',
  wallet:'<rect x="3" y="5" width="18" height="15" rx="2"/><path d="M3 8V5l14-3v3M21 11h-6v5h6"/><path d="M17 13.5h.01"/>',
  sliders:'<path d="M4 7h7m4 0h5M4 17h3m4 0h9"/><circle cx="13" cy="7" r="2"/><circle cx="9" cy="17" r="2"/>',
  info:'<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7h.01"/>',
  'arrow-down':'<path d="M12 4v16m-6-6 6 6 6-6"/>',
  'arrow-up':'<path d="M12 20V4m-6 6 6-6 6 6"/>',
  external:'<path d="M14 4h6v6m0-6-9 9M10 4H5a1 1 0 0 0-1 1v14a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-5"/>',
  close:'<path d="m6 6 12 12M6 18 18 6"/>',
  chevron:'<path d="m6 9 6 6 6-6"/>',
  reset:'<path d="M3 10a9 9 0 1 1 2 8M3 4v6h6"/>',
  download:'<path d="M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5"/>',
  phone:'<path d="m5 3 4 1 1 5-3 2a15 15 0 0 0 6 6l2-3 5 1 1 4c-1 4-7 2-12-3S2 4 5 3Z"/>',
  chat:'<path d="M21 11a9 9 0 0 1-13 8l-5 2 1-6A9 9 0 1 1 21 11Z"/><path d="M8 10h8M8 14h5"/>',
  globe:'<circle cx="12" cy="12" r="9"/><ellipse cx="12" cy="12" rx="4" ry="9"/><path d="M3 12h18"/>',
  app:'<rect x="6" y="2" width="12" height="20" rx="2"/><path d="M10 5h4M11 19h2"/>',
  calendar:'<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M7 3v4M17 3v4M3 10h18M8 14h2M14 14h2M8 17h2"/>'
};
const icon=name=>`<svg class="icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">${icons[name]||icons.court}</svg>`;
const escapeHTML=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const n=value=>Number(value).toLocaleString('ar-SA');
const normalize=value=>String(value).normalize('NFKC').replace(/[\u064B-\u065F\u0670\u0640]/g,'').replace(/[أإآ]/g,'ا').replace(/ى/g,'ي').replace(/ة/g,'ه').toLowerCase().trim();
const courts=window.COURTS_DATA||[];
const $=id=>document.getElementById(id);
let filter='all',saved=new Set(),toastTimer;
const storageKey='riyadh-tennis:saved:v1';
try{const data=JSON.parse(localStorage.getItem(storageKey)||'[]');if(Array.isArray(data))saved=new Set(data.filter(id=>courts.some(c=>c.id===id)));}catch{/* Browsing still works when persistence is unavailable. */}
const validContacts=c=>c.booking.contacts.filter(p=>p.e164&&p.formatStatus==='plausible');
const hourPrice=c=>{const prices=c.prices.filter(p=>p.durationMinutes===60&&p.currencyStatus==='recorded');return prices.length?Math.min(...prices.map(p=>p.amount)):null;};
const duration=minutes=>minutes===60?'ساعة':minutes===90?'ساعة ونصف':minutes===120?'ساعتان':minutes?`${n(minutes)} دقيقة`:'مدة غير محددة';
function safeUrl(url){try{const u=new URL(url);return ['https:','tel:'].includes(u.protocol)?u.href:'#';}catch{return '#';}}
function link(url,label,symbol,cls=''){const phone=url.startsWith('tel:');return `<a class="${cls}" href="${escapeHTML(safeUrl(url))}"${phone?'':' target="_blank" rel="noopener noreferrer"'}>${icon(symbol)}<span>${escapeHTML(label)}</span>${phone?'':'<span class="sr-only"> (يفتح في نافذة جديدة)</span>'}</a>`;}
function matches(c,type){return type==='all'||type==='priced'&&c.prices.length>0||type==='shared'&&c.map.kind==='shared_link'||type==='saved'&&saved.has(c.id);}
function bookingMatches(c,type){return type==='all'||type==='contact'&&validContacts(c).length>0||type==='online'&&c.booking.links.some(l=>l.type==='booking')||type==='app'&&c.booking.method.includes('تطبيق')||type==='website'&&c.booking.links.some(l=>l.type==='website');}
function priceMarkup(c){
 if(!c.prices.length)return '<div class="price-main"><span class="price-unknown">السعر غير مسجّل</span></div><p class="price-sub">استفسر من المنشأة قبل الحجز</p>';
 const timed=c.prices.some(p=>p.timeWindow);const p=timed?[...c.prices].sort((a,b)=>a.amount-b.amount)[0]:c.prices[0];
 const sub=p.durationMinutes===null?'مدة هذا السعر تحتاج تأكيدًا':timed?'يختلف السعر بين الذروة وخارجها':p.durationMinutes===120?`ما يعادل ${n(p.amount/2)} ريال / ساعة · الحجز ساعتان`:c.prices.length>1?'خيارات مدد إضافية · التفاصيل أدناه':'سعر مسجّل · يُؤكّد عند الحجز';
 return `<div class="price-main">${timed?'<span class="from">من</span>':''}<strong class="price-amount">${n(p.amount)}</strong><span class="price-unit">ريال${p.durationMinutes?' / '+duration(p.durationMinutes):''}</span></div><p class="price-sub ${p.durationMinutes===null?'warning':''}">${sub}</p>`;
}
function cardMarkup(c){
 const contacts=validContacts(c),online=c.booking.links.find(l=>l.type==='booking'),site=c.booking.links.find(l=>l.type==='website'),apps=c.booking.links.filter(l=>['android','ios'].includes(l.type));
 let primary='';
 if(online)primary=link(online.url,'انتقل للحجز','calendar','action primary');
 else if(contacts.length){const p=contacts[0];primary=link(p.type==='whatsapp'?'https://wa.me/'+p.e164.slice(1):'tel:'+p.e164,p.type==='whatsapp'?'تواصل عبر واتساب':'اتصل للحجز',p.type==='whatsapp'?'chat':'phone','action primary');}
 else if(apps.length)primary=apps.map(a=>link(a.url,a.label,'app','action primary')).join('');
 else if(site)primary=link(site.url,'موقع المنشأة','globe','action primary');
 const kind=c.map.kind,mapLabel=kind==='search'?'بحث بالخريطة':kind==='coordinates'?'إحداثيات المنشأة':'رابط موقع مشارَك';
 const mapAction=link(c.map.url,kind==='search'?'بحث بالخريطة':'عرض الموقع','pin',`action ${primary?'':'primary'}`);
 const detailsLinks=[...c.booking.links.map(l=>link(l.url,l.type==='booking'?'صفحة الحجز':l.label,l.type==='booking'?'calendar':l.type==='website'?'globe':'app')),...contacts.map(p=>link(p.type==='whatsapp'?'https://wa.me/'+p.e164.slice(1):'tel:'+p.e164,p.type==='whatsapp'?'واتساب':'اتصال',p.type==='whatsapp'?'chat':'phone'))].join('');
 const invalid=c.booking.contacts.filter(p=>!p.e164).map(p=>`<p class="issue">رقم التواصل يحتاج مراجعة: <bdi dir="ltr">+${escapeHTML(p.raw)}</bdi>. لم يُفعّل رابط التواصل.</p>`).join('');
 return `<article class="card" data-id="${c.id}" aria-labelledby="name-${c.id}"><div class="card-body"><div class="card-top"><span class="venue-icon">${icon('court')}</span><span class="map-badge">${icon(kind==='search'?'search':'pin')}${mapLabel}</span><button class="icon-button save-button" data-save="${c.id}" aria-label="${saved.has(c.id)?'إزالة':'حفظ'} ${escapeHTML(c.name)}${saved.has(c.id)?' من المحفوظة':''}" aria-pressed="${saved.has(c.id)}">${icon('bookmark')}</button></div><h3 id="name-${c.id}">${escapeHTML(c.name)}</h3><p class="location">${icon('pin')}${escapeHTML(c.locationText||'المنطقة غير مسجّلة')}</p><div class="price-block">${priceMarkup(c)}</div><p class="booking-method">${icon(c.booking.method.includes('واتساب')?'chat':c.booking.method.includes('تطبيق')?'app':'calendar')}<span>الحجز: <b>${escapeHTML(c.booking.method)}${invalid?' · الرقم يحتاج مراجعة':''}</b></span></p><details class="card-details"><summary>التفاصيل والأسعار ${icon('chevron')}</summary><div class="expanded">${c.prices.length?`<table class="price-table" aria-label="أسعار ${escapeHTML(c.name)}"><tbody>${c.prices.map(p=>`<tr><td>${escapeHTML(p.label||duration(p.durationMinutes))}${p.timeWindow?`<small>${escapeHTML(p.timeWindow)} · للساعة</small>`:''}</td><td>${n(p.amount)} ريال</td></tr>`).join('')}</tbody></table>`:''}<p>${escapeHTML(c.notes)}</p>${invalid}${c.issues.includes('currency_assumed')?'<p class="issue">عملة الأسعار مفترضة بالريال؛ تحتاج تأكيدًا.</p>':''}<p>${kind==='search'?'الرابط يبحث باسم المنشأة؛ الموقع ومدخل الملعب غير مؤكدين.':kind==='coordinates'?'الإحداثيات تخص المنشأة؛ مدخل الملعب غير مؤكد.':'الرابط من السجل الأصلي؛ مدخل الملعب لم يُتحقق منه.'}</p><div class="secondary-links">${detailsLinks}</div></div></details></div><div class="actions">${primary}${mapAction}</div></article>`;
}
function updateSaved(){ $('saved-count').textContent=n(saved.size); }
function showToast(message){clearTimeout(toastTimer);$('toast').textContent=message;$('toast').classList.add('visible');toastTimer=setTimeout(()=>$('toast').classList.remove('visible'),2500);}
function render(){
 const query=normalize($('search').value),booking=$('booking-filter').value,sort=$('sort').value;
 let list=courts.filter(c=>matches(c,filter)&&bookingMatches(c,booking)&&query.split(/\s+/).every(word=>normalize([c.name,c.locationText,c.booking.method].join(' ')).includes(word)));
 if(sort==='name')list.sort((a,b)=>a.name.localeCompare(b.name,'ar'));
 if(sort.startsWith('price'))list.sort((a,b)=>{const x=hourPrice(a),y=hourPrice(b);return x===null?(y===null?0:1):y===null?-1:sort==='price-asc'?x-y:y-x;});
 $('courts').innerHTML=list.map(cardMarkup).join('')||`<div class="empty">${icon(filter==='saved'?'bookmark':'search')}<h3>${filter==='saved'&&!saved.size?'ملاعبك المفضلة تبدأ من هنا':'لا توجد ملاعب مطابقة'}</h3><p>${filter==='saved'&&!saved.size?'اضغط علامة الحفظ على أي ملعب لتجده هنا.':'جرّب اسمًا آخر أو وسّع خيارات التصفية.'}</p><button id="empty-reset">عرض كل الملاعب</button></div>`;
 $('result-count').textContent=`عرض ${n(list.length)} من ${n(courts.length)} ملعب ومنشأة`;
 $('clear-search').hidden=!$('search').value;$('reset-filters').hidden=!(query||filter!=='all'||booking!=='all'||sort!=='default');$('sort-note').hidden=!sort.startsWith('price');
 document.querySelectorAll('[data-filter]').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.filter===filter)));
 if($('empty-reset'))$('empty-reset').addEventListener('click',()=>{reset();$('search').focus();});
 updateSaved();
}
function reset(){filter='all';$('search').value='';$('booking-filter').value='all';$('sort').value='default';render();}
document.querySelectorAll('[data-icon]').forEach(el=>el.innerHTML=icon(el.dataset.icon));
$('total-stat').textContent=n(courts.length);$('price-stat').textContent=n(courts.filter(c=>c.prices.length).length);$('all-count').textContent=n(courts.length);
$('search').addEventListener('input',render);$('booking-filter').addEventListener('change',render);$('sort').addEventListener('change',render);
$('clear-search').addEventListener('click',()=>{$('search').value='';render();$('search').focus();});$('reset-filters').addEventListener('click',()=>{reset();$('search').focus();});
document.querySelectorAll('[data-filter]').forEach(button=>button.addEventListener('click',()=>{filter=button.dataset.filter;render();}));
$('saved-nav').addEventListener('click',()=>{reset();filter='saved';render();$('directory').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});document.querySelector('[data-filter="saved"]').focus({preventScroll:true});});
$('courts').addEventListener('click',event=>{const button=event.target.closest('[data-save]');if(!button)return;const id=button.dataset.save;const adding=!saved.has(id);adding?saved.add(id):saved.delete(id);let persisted=true;try{localStorage.setItem(storageKey,JSON.stringify([...saved]));}catch{persisted=false;}
 if(filter==='saved'){render();const next=document.querySelector('[data-save]')||$('empty-reset');if(next)next.focus();}else{button.setAttribute('aria-pressed',String(adding));const c=courts.find(c=>c.id===id);button.setAttribute('aria-label',`${adding?'إزالة':'حفظ'} ${c.name}${adding?' من المحفوظة':''}`);updateSaved();}
 showToast(persisted?(adding?'تم حفظ الملعب على هذا الجهاز':'تمت إزالة الملعب من المحفوظة'):'الحفظ متاح لهذه الجلسة فقط');
});
render();
