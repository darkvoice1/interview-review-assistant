import { createRouter, createWebHistory } from "vue-router";

import DocumentsView from "../views/DocumentsView.vue";
import HomeView from "../views/HomeView.vue";
import ReviewView from "../views/ReviewView.vue";
import WrongQuestionsView from "../views/WrongQuestionsView.vue";

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
];

export default createRouter({
  history: createWebHistory(),
  routes,
});
