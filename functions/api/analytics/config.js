const jsonHeaders = {
  "cache-control": "no-store",
  "content-type": "application/json; charset=utf-8",
};

function validMeasurementId(value) {
  return typeof value === "string" && /^G-[A-Z0-9]+$/.test(value.trim());
}

export async function onRequestGet({ env }) {
  const measurementId = env.PUBLIC_GA_MEASUREMENT_ID || env.GA_MEASUREMENT_ID || "";
  return new Response(
    JSON.stringify({
      gaMeasurementId: validMeasurementId(measurementId) ? measurementId.trim() : "",
      gscVerificationConfigured: Boolean(env.PUBLIC_GOOGLE_SITE_VERIFICATION || env.GOOGLE_SITE_VERIFICATION),
    }),
    { headers: jsonHeaders },
  );
}

