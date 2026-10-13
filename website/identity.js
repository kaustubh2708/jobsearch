/* Shared job identity helper for Orbit v1 and v2.
   Keep in sync with CLAUDE.md: "Changing it orphans saved state, so do not change casually." */
(() => {
  const IDP = ["jk", "gh_jid", "jobid", "job_id", "requisitionid", "reqid", "folderid", "id"];
  const norm = value => String(value || "").trim().toLocaleLowerCase().replace(/[.,]/g, "").replace(/\s+/g, " ");

  function jobIdentity(job) {
    if (job && job.url) {
      try {
        const u = new URL(job.url);
        const q = IDP.map(k => [k, u.searchParams.get(k)]).filter(x => x[1]).map(x => x.join("=")).join("&");
        return `url:${u.hostname.toLowerCase()}${u.pathname.replace(/\/$/, "")}${q ? "?" + q : ""}`;
      } catch (_) {}
    }
    return `role:${norm(job?.company)}|${norm(job?.title)}|${norm(job?.location)}`;
  }

  window.jobIdentity = jobIdentity;
  window.OrbitJobIdentity = { jobIdentity, IDP, norm };
})();
