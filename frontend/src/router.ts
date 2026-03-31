import { createRouter, createWebHistory } from "vue-router";
import DashboardView from "./views/DashboardProView.vue";
import EventsView from "./views/EventsProView.vue";
import ReportsView from "./views/ReportsProView.vue";
import AssistantView from "./views/AssistantProView.vue";

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", component: DashboardView },
    { path: "/events", component: EventsView },
    { path: "/reports", component: ReportsView },
    { path: "/assistant", component: AssistantView }
  ]
});
