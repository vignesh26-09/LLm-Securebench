import { BackendUnavailable } from "../components/common/AsyncState";

export function UnavailablePage({ title, endpoint, description }: { title: string; endpoint: string; description: string }) {
  return <section><h1>{title}</h1><p>{description}</p><BackendUnavailable resource={title} endpoint={endpoint} /></section>;
}
