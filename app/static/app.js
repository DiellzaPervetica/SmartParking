const { createApp } = Vue;

const ZoneBlock = {
  props: {
    title: String,
    spots: Array,
    view: String,
  },
  methods: {
    spotClass(spot) {
      return {
        occupied: spot.occupied,
        free: !spot.occupied,
        anomaly: spot.anomaly_label !== "normal",
      };
    },
    percent(value) {
      return `${Math.round((value || 0) * 100)}%`;
    },
  },
  template: `
    <section class="zone-block">
      <div class="zone-title">
        <strong>{{ title }}</strong>
        <span>{{ spots.filter((spot) => !spot.occupied).length }} te lira</span>
      </div>
      <div class="spot-grid">
        <article
          v-for="spot in spots"
          :key="spot.spot_id"
          class="spot"
          :class="spotClass(spot)"
        >
          <span class="spot-id">{{ spot.spot_id }}</span>
          <div v-if="view === 'plan'" class="spot-visual">
            <img
              v-if="spot.occupied"
              class="car-image"
              src="/images/car.png"
              alt=""
              aria-hidden="true"
              draggable="false"
            />
          </div>
          <div v-else-if="view === 'sensors'" class="spot-data">
            <span>{{ Math.round(spot.distance_cm) }} cm</span>
            <span>{{ Math.round(spot.battery_level) }}%</span>
            <span>{{ spot.signal_strength }} dBm</span>
          </div>
          <div v-else class="spot-data">
            <span>{{ spot.classification_label }}</span>
            <span>{{ spot.anomaly_label }}</span>
            <span>{{ percent(spot.anomaly_score) }}</span>
          </div>
        </article>
      </div>
    </section>
  `,
};

createApp({
  components: {
    ZoneBlock,
  },
  data() {
    return {
      snapshot: null,
      loading: true,
      error: null,
      view: "plan",
      scenario: "auto",
      autoRefresh: true,
      timer: null,
      scenarios: [
        { value: "auto", label: "Auto" },
        { value: "morning_peak", label: "Peak mengjes" },
        { value: "afternoon_peak", label: "Peak pasdite" },
        { value: "evening_relief", label: "Mbremje" },
        { value: "maintenance", label: "Mirembajtje" },
      ],
    };
  },
  computed: {
    summary() {
      return this.snapshot?.summary || {};
    },
  },
  watch: {
    scenario() {
      this.load();
    },
    autoRefresh() {
      this.schedule();
    },
  },
  mounted() {
    this.load();
    this.schedule();
  },
  beforeUnmount() {
    this.clearTimer();
  },
  methods: {
    async load() {
      this.loading = true;
      this.error = null;
      try {
        const response = await fetch(`/parking/dashboard-data?scenario=${encodeURIComponent(this.scenario)}`, {
          headers: { Accept: "application/json" },
        });
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        this.snapshot = await response.json();
      } catch (error) {
        this.error = "Nuk u lexua endpoint-i i simulimit.";
        console.error(error);
      } finally {
        this.loading = false;
      }
    },
    schedule() {
      this.clearTimer();
      if (this.autoRefresh) {
        this.timer = window.setInterval(() => this.load(), 6000);
      }
    },
    clearTimer() {
      if (this.timer) {
        window.clearInterval(this.timer);
        this.timer = null;
      }
    },
    zoneSpots(zoneId) {
      return (this.snapshot?.spots || []).filter((spot) => spot.zone_id === zoneId);
    },
    percent(value) {
      return `${Math.round((value || 0) * 100)}%`;
    },
    money(value) {
      return `${Number(value || 0).toFixed(2)} EUR`;
    },
  },
}).mount("#app");
