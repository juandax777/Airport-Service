(() => {
  const page = document.body.dataset.page;
  const clean = (value) =>
    String(value ?? "").replace(/[&<>'"]/g, (char) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[char],
    );

  const getAirports = async () => {
    const response = await fetch("/ui-api/airports");
    if (!response.ok) throw new Error("No fue posible cargar los aeropuertos");
    return response.json();
  };

  if (page === "dashboard") {
    getAirports()
      .then((airports) => {
        const byId = new Map(airports.map((airport) => [String(airport.id), airport]));
        const points = airports.filter(
          (airport) => airport.latitude != null && airport.longitude != null,
        );
        const panel = document.querySelector("#selected-airport");

        const choose = (id) => {
          const airport = byId.get(String(id));
          if (!airport) return;
          document.querySelector("#selected-airport-name").textContent = airport.name;
          document.querySelector("#selected-airport-city").textContent =
            `${airport.city || "Ciudad no disponible"} · ID ${airport.id}`;
          document.querySelector("#plan-itinerary").href =
            `/itineraries/new?arrival_id=${encodeURIComponent(airport.id)}`;
          panel.hidden = false;
          panel.scrollIntoView({ behavior: "smooth", block: "nearest" });
        };

        const list = document.querySelector("#airport-list");
        const enhanceList = () => {
          if (!list || list.querySelector("[data-destination-id]")) return false;
          list.innerHTML = airports
            .slice(0, 20)
            .map(
              (airport) =>
                `<button type="button" class="airport-card" data-destination-id="${clean(airport.id)}"><strong>${clean(airport.name)}</strong><span>${clean(airport.city || "Ciudad no disponible")} · ID ${clean(airport.id)}</span><em>Elegir como llegada →</em></button>`,
            )
            .join("");
          return true;
        };

        const listTimer = setInterval(() => {
          if (enhanceList()) clearInterval(listTimer);
        }, 100);

        list?.addEventListener("click", (event) => {
          const button = event.target.closest("[data-destination-id]");
          if (button) choose(button.dataset.destinationId);
        });

        const map = document.querySelector("#airport-map");
        const mapTimer = setInterval(() => {
          if (typeof map?.on !== "function") return;
          clearInterval(mapTimer);
          map.on("plotly_click", (event) => {
            const point = event.points?.[0];
            if (!point) return;
            // map-coordinate-fix stores the real airport ID in Plotly customdata.
            // The positional fallback keeps compatibility while the graph initializes.
            choose(point.customdata ?? points[point.pointNumber]?.id);
          });
        }, 100);
      })
      .catch(() => {});
  }

  if (page === "form") {
    const arrivalId = new URLSearchParams(location.search).get("arrival_id");
    if (!arrivalId) return;
    getAirports()
      .then((airports) => {
        const airport = airports.find((item) => String(item.id) === arrivalId);
        if (!airport) return;
        const timer = setInterval(() => {
          const select = document.querySelector('[name="arrival_airport_id"]');
          if (!select?.querySelector(`option[value="${CSS.escape(arrivalId)}"]`)) return;
          clearInterval(timer);
          select.value = arrivalId;
          select.dispatchEvent(new Event("change", { bubbles: true }));
          const notice = document.querySelector("#arrival-choice");
          document.querySelector("#arrival-choice-name").textContent =
            `${airport.name} — ${airport.city || "Sin ciudad"}`;
          notice.hidden = false;
        }, 100);
      })
      .catch(() => {});
  }
})();
