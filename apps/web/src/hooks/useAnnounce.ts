import { useAnnouncerContext } from '../context/AnnouncerContext';

export function useAnnounce() {
  return useAnnouncerContext();
}
