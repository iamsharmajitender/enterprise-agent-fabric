import { jobElements, mountJobs } from "./jobs.js";
import { wireOpenInNewTabLinks } from "./nav.js";

wireOpenInNewTabLinks();
void mountJobs(jobElements());
