/**
 * Polls getStatus every 5 s (react-query refetchInterval). Renders one pill per component in response
 * order: text = component name, data-ok="true|false", green when ok, red when not with title = detail.
 * While loading: "Checking services…". Request error: one red pill "api" with the error message.
 */
export function StatusBar(): React.ReactElement {
  throw new Error('not implemented')
}
