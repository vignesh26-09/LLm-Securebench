import { useQuery } from "@tanstack/react-query";
import { apiClient } from "./client";

export function useHealth() {
  return useQuery({ queryKey: ["health"], queryFn: apiClient.health, retry: false, refetchInterval: 15000 });
}

export function useReadiness() {
  return useQuery({ queryKey: ["ready"], queryFn: apiClient.ready, retry: false, refetchInterval: 15000 });
}

export function useScientificRecords(family?: string, limit = 25, offset = 0) {
  return useQuery({
    queryKey: ["scientific-records", family, limit, offset],
    queryFn: () => apiClient.scientificRecords({ family, limit, offset }),
    retry: false,
  });
}

export function useModelScores(limit = 10, offset = 0) {
  return useQuery({
    queryKey: ["model-scores", limit, offset],
    queryFn: () => apiClient.modelScores(limit, offset),
    retry: false,
  });
}
