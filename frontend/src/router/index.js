import { createRouter, createWebHistory } from "vue-router";

import HomeView from "../views/HomeView.vue";
import DocumentsView from "../views/DocumentsView.vue";
import ReviewView from "../views/ReviewView.vue";
import WrongQuestionsView from "../views/WrongQuestionsView.vue";
import StatisticsView from "../views/StatisticsView.vue";

const routes = [
  {
    path: "/",
    name: "home",
    component: HomeView,
  },
  {
    path: "/documents",
    name: "documents",
    component: DocumentsView,
  },
  {
    path: "/review",
    name: "review",
    component: ReviewView,
  },
  {
    path: "/wrong-questions",
    name: "wrong-questions",
    component: WrongQuestionsView,
  },
  {
    path: "/statistics",
    name: "statistics",
    component: StatisticsView,
  },
];

export default createRouter({
  history: createWebHistory(),
  routes,
});
