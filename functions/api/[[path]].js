import { handleRequest } from "../../serverless/worker.js";

export const onRequest = ({ request, env }) => handleRequest(request, env);
