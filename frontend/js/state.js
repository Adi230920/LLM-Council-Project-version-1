// js/state.js
/**
 * Simple centralized state management for the application.
 */

export const AppState = {
  isRequesting: false,
  theme: localStorage.getItem('bouleAI_theme') || 'dark', // default to dark
  hasSeenOnboarding: localStorage.getItem('bouleAI_onboarded') === 'true',
};

export function setTheme(newTheme) {
  AppState.theme = newTheme;
  localStorage.setItem('bouleAI_theme', newTheme);
  document.documentElement.setAttribute('data-theme', newTheme);
}

export function setOnboarded() {
  AppState.hasSeenOnboarding = true;
  localStorage.setItem('bouleAI_onboarded', 'true');
}

export function setRequesting(status) {
  AppState.isRequesting = status;
}
