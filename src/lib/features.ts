import { type LGUConfig, config } from './lguConfig';

export type FeatureName = keyof LGUConfig['features'];

/**
 * Route prefixes owned by each feature flag in config/lgu.config.json.
 * The admin area only manages legislative records, so it follows openLGU.
 */
const FEATURE_PATHS: Record<FeatureName, string[]> = {
  openLGU: ['/openlgu', '/admin'],
  transparency: ['/transparency'],
  statistics: ['/statistics'],
  tourism: ['/tourism'],
};

export function isFeatureEnabled(feature: FeatureName): boolean {
  return config.features[feature] !== false;
}

/**
 * False when an internal path belongs to a disabled feature.
 * External URLs and paths no feature owns are always enabled.
 */
export function isPathEnabled(href: string): boolean {
  if (!href.startsWith('/')) return true;
  const path = href.split(/[?#]/)[0];

  return (Object.keys(FEATURE_PATHS) as FeatureName[]).every(
    feature =>
      isFeatureEnabled(feature) ||
      !FEATURE_PATHS[feature].some(
        prefix => path === prefix || path.startsWith(`${prefix}/`)
      )
  );
}
