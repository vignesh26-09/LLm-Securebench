const parsed = Number(import.meta.env.VITE_SECURELLM_PAGE_SIZE ?? "25");
export const pageSize = Number.isInteger(parsed) && parsed > 0 && parsed <= 100 ? parsed : 25;
export const scientificMaturityLabel = "NOT VALIDATED";
