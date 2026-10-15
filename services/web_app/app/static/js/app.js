const $=(selector,root=document)=>root.querySelector(selector);const $$=(selector,root=document)=>[...root.querySelectorAll(selector)];
const page=document.body.dataset.page,itemId=document.body.dataset.itemId,mode=document.body.dataset.mode;
const errorMessage = (detail) => {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        const field = item?.loc?.at(-1);
        const label = field === "duration_minutes" ? "Duración estimada" : field;
        const message = item?.msg;
        if (!message) return JSON.stringify(item);
        return label ? `${label}: ${message}` : message;
      })
      .join("; ");
  }
  if (detail && typeof detail === "object") {
    return detail.msg || detail.message || JSON.stringify(detail);
  }
  return "No fue posible completar la operación.";
};
const api=async(url,options={})=>{const response=await fetch(url,{headers:{"Content-Type":"application/json"},...options});if(response.status===204)return null;const data=await response.json().catch(()=>({detail:"Respuesta inválida"}));if(!response.ok)throw new Error(errorMessage(data.detail));return data};
const escapeHtml=value=>String(value??"").replace(/[&<>'"]/g,char=>({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[char]));
const showToast=message=>{const toast=$("#toast");toast.textContent=message;toast.classList.add("show");setTimeout(()=>toast.classList.remove("show"),2600)};
const prettyDate=value=>new Intl.DateTimeFormat("es-CO",{dateStyle:"long",timeZone:"UTC"}).format(new Date(`${value}T00:00:00Z`));

async function loadDashboard(){const list=$("#airport-list"),error=$("#map-error");try{const airports=await api("/ui-api/airports");$("#airport-count").textContent=`${airports.length} aeropuertos`;const render=items=>list.innerHTML=items.slice(0,20).map(a=>`<article class="airport-card"><strong>${escapeHtml(a.name)}</strong><span>${escapeHtml(a.city||"Ciudad no disponible")} · ID ${escapeHtml(a.id)}</span></article>`).join("")||"<p class='muted'>No encontramos resultados.</p>";render(airports);$("#airport-search").addEventListener("input",e=>{const q=e.target.value.toLowerCase();render(airports.filter(a=>`${a.name} ${a.city}`.toLowerCase().includes(q)))});const points=airports.filter(a=>a.latitude!=null&&a.longitude!=null);if(window.Plotly&&points.length)Plotly.newPlot("airport-map",[{type:"scattergeo",mode:"markers",lat:points.map(a=>a.latitude),lon:points.map(a=>a.longitude),text:points.map(a=>`${a.name}<br>${a.city||""}`),marker:{size:9,color:"#126b63",line:{color:"#fff",width:1}}}],{margin:{t:0,r:0,b:0,l:0},geo:{scope:"south america",projection:{type:"mercator"},center:{lat:4.5,lon:-74},lataxis:{range:[-5,14]},lonaxis:{range:[-82,-66]},showland:true,landcolor:"#eef3f1",showcountries:true,countrycolor:"#bccac6",bgcolor:"#eaf1ef"}},{responsive:true,displayModeBar:false})}catch(err){list.innerHTML=`<div class="message message-error">${escapeHtml(err.message)}</div>`;error.textContent=err.message;error.hidden=false}}
async function loadItineraries(){const container=$("#itinerary-list");try{const items=await api("/ui-api/itineraries");$("#itinerary-count").textContent=`${items.length} registrados`;const render=rows=>container.innerHTML=rows.length?`<table><thead><tr><th>Viajero</th><th>Ruta</th><th>Fecha</th><th>Duración</th><th></th></tr></thead><tbody>${rows.map(i=>`<tr><td>${escapeHtml(i.user_name)}</td><td>${escapeHtml(i.departure_airport_id)} → ${escapeHtml(i.arrival_airport_id)}</td><td>${prettyDate(i.travel_date)}</td><td>${i.duration_minutes} min</td><td><a href="/itineraries/${encodeURIComponent(i.id)}">Ver detalle</a></td></tr>`).join("")}</tbody></table>`:`<div class="empty-state"><h2>Aún no hay viajes</h2><p>Crea tu primer itinerario para verlo aquí.</p><a class="button button-primary" href="/itineraries/new">Crear itinerario</a></div>`;render(items);$("#itinerary-search").addEventListener("input",e=>{const q=e.target.value.toLowerCase();render(items.filter(i=>`${i.user_name} ${i.departure_airport_id} ${i.arrival_airport_id}`.toLowerCase().includes(q)))})}catch(err){container.innerHTML=`<div class="message message-error">${escapeHtml(err.message)}</div>`}}
async function loadForm() {
  const form = $("#itinerary-form");
  const submit = $("#submit-button");
  const error = $("#form-error");
  const duration = form.elements.namedItem("duration_minutes");
  const durationHelp = $("#duration-estimate-help");
  let airports = [];

  const estimateDuration = (departureId, arrivalId) => {
    const departure = airports.find((airport) => String(airport.id) === String(departureId));
    const arrival = airports.find((airport) => String(airport.id) === String(arrivalId));
    if (
      !departure ||
      !arrival ||
      departure.latitude == null ||
      departure.longitude == null ||
      arrival.latitude == null ||
      arrival.longitude == null
    ) {
      return null;
    }

    const departureLatitude = Number(departure.latitude);
    const departureLongitude = Number(departure.longitude);
    const arrivalLatitude = Number(arrival.latitude);
    const arrivalLongitude = Number(arrival.longitude);
    const coordinates = [departureLatitude, departureLongitude, arrivalLatitude, arrivalLongitude];
    if (
      coordinates.some((coordinate) => !Number.isFinite(coordinate)) ||
      Math.abs(departureLatitude) > 90 ||
      Math.abs(arrivalLatitude) > 90 ||
      Math.abs(departureLongitude) > 180 ||
      Math.abs(arrivalLongitude) > 180
    ) {
      return null;
    }

    const toRadians = (value) => (value * Math.PI) / 180;
    const latitude1 = toRadians(departureLatitude);
    const latitude2 = toRadians(arrivalLatitude);
    const latitudeDifference = latitude2 - latitude1;
    const longitudeDifference = toRadians(arrivalLongitude - departureLongitude);
    const haversine =
      Math.sin(latitudeDifference / 2) ** 2 +
      Math.cos(latitude1) *
        Math.cos(latitude2) *
        Math.sin(longitudeDifference / 2) ** 2;
    const boundedHaversine = Math.min(1, Math.max(0, haversine));
    const distanceKm =
      6371.0088 *
      2 *
      Math.atan2(Math.sqrt(boundedHaversine), Math.sqrt(1 - boundedHaversine));

    // Approximate at 750 km/h, with a 30-minute allowance for climb and airport time.
    return Math.max(30, Math.ceil((distanceKm / 750 * 60 + 30) / 5) * 5);
  };

  const updateEstimate = () => {
    const departureId = form.elements.namedItem("departure_airport_id").value;
    const arrivalId = form.elements.namedItem("arrival_airport_id").value;
    const minutes = estimateDuration(departureId, arrivalId);
    duration.value = minutes ?? "";

    if (minutes) {
      durationHelp.textContent = `Aproximadamente ${minutes} minutos. Se estima con la distancia entre aeropuertos; el tiempo real puede variar.`;
    } else if (!departureId || !arrivalId) {
      durationHelp.textContent = "Selecciona ambos aeropuertos para calcular el tiempo aproximado del vuelo.";
    } else {
      durationHelp.textContent = "No hay coordenadas disponibles para estimar esta ruta.";
    }
  };

  try {
    airports = await api("/ui-api/airports");
    for (const select of $$("select", form)) {
      select.insertAdjacentHTML(
        "beforeend",
        airports
          .map(
            (airport) =>
              `<option value="${escapeHtml(airport.id)}">${escapeHtml(airport.name)} — ${escapeHtml(airport.city || "Sin ciudad")}</option>`,
          )
          .join(""),
      );
    }
    if (mode === "edit") {
      const item = await api(`/ui-api/itineraries/${itemId}`);
      for (const [key, value] of Object.entries(item)) {
        const field = form.elements.namedItem(key);
        if (field) field.value = value;
      }
    }
  } catch (err) {
    error.textContent = err.message;
    error.hidden = false;
  }

  form.elements.namedItem("departure_airport_id").addEventListener("change", updateEstimate);
  form.elements.namedItem("arrival_airport_id").addEventListener("change", updateEstimate);
  updateEstimate();

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    error.hidden = true;
    if (!form.reportValidity()) return;

    const data = Object.fromEntries(new FormData(form));
    const durationMinutes = Number(data.duration_minutes);
    if (!Number.isInteger(durationMinutes) || durationMinutes < 1) {
      error.textContent = "No se pudo estimar la duración de esta ruta. Comprueba los aeropuertos seleccionados e inténtalo de nuevo.";
      error.hidden = false;
      return;
    }
    data.duration_minutes = durationMinutes;

    if (data.departure_airport_id === data.arrival_airport_id) {
      error.textContent = "Salida y llegada deben ser diferentes.";
      error.hidden = false;
      return;
    }

    submit.disabled = true;
    submit.textContent = "Guardando…";
    try {
      const url = mode === "edit" ? `/ui-api/itineraries/${itemId}` : "/ui-api/itineraries";
      const saved = await api(url, {
        method: mode === "edit" ? "PUT" : "POST",
        body: JSON.stringify(data),
      });
      location.href = `/itineraries/${saved.id}`;
    } catch (err) {
      error.textContent = err.message;
      error.hidden = false;
      submit.disabled = false;
      submit.textContent = mode === "edit" ? "Guardar cambios" : "Crear itinerario";
    }
  });
}
async function loadDetail(){const root=$("#detail-content");try{const i=await api(`/ui-api/itineraries/${itemId}`);root.innerHTML=`<article class="panel detail-card"><div class="detail-header"><div><p class="eyebrow">Itinerario confirmado</p><h1>${escapeHtml(i.user_name)}</h1><p class="muted">Identificador ${escapeHtml(i.id)}</p></div><span class="badge">Registrado</span></div><div class="detail-grid"><div class="detail-item"><span>Salida</span><strong>${escapeHtml(i.departure_airport_id)}</strong></div><div class="detail-item"><span>Llegada</span><strong>${escapeHtml(i.arrival_airport_id)}</strong></div><div class="detail-item"><span>Fecha</span><strong>${prettyDate(i.travel_date)}</strong></div><div class="detail-item"><span>Duración</span><strong>${i.duration_minutes} minutos</strong></div></div><div class="form-actions"><button class="button button-danger" id="delete-button">Eliminar</button><a class="button button-primary" href="/itineraries/${encodeURIComponent(i.id)}/edit">Editar itinerario</a></div></article>`;const dialog=$("#delete-dialog");$("#delete-button").onclick=()=>dialog.showModal();$("[data-close]").onclick=()=>dialog.close();$("#confirm-delete").onclick=async()=>{await api(`/ui-api/itineraries/${itemId}`,{method:"DELETE"});showToast("Itinerario eliminado");setTimeout(()=>location.href="/itineraries",400)}}catch(err){root.innerHTML=`<div class="message message-error">${escapeHtml(err.message)}</div>`}}
if(page==="dashboard")loadDashboard();if(page==="itineraries")loadItineraries();if(page==="form")loadForm();if(page==="detail")loadDetail();
