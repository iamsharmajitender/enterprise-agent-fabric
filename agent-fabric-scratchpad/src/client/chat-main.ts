import { chatElements, mountChat } from "./chat.js";
import { wireOpenInNewTabLinks } from "./nav.js";

wireOpenInNewTabLinks();
void mountChat(chatElements());
