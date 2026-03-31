import { createRouter, createWebHistory } from "vue-router";
import DashboardView from "./views/DashboardCnView.vue";
import EventsView from "./views/EventsCnView.vue";
import ReportsView from "./views/ReportsCnView.vue";
import AssistantView from "./views/AssistantCnView.vue";

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", component: DashboardView },
    { path: "/events", component: EventsView },
    { path: "/reports", component: ReportsView },
    { path: "/assistant", component: AssistantView }
  ]
});
