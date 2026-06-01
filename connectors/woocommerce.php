<?php
/**
 * WooCommerce connector (example).
 * Validate the delivery address against Pinpoint at checkout, server-side.
 * Drop into your theme's functions.php or a small plugin and set PINPOINT_KEY.
 */

const PINPOINT_BASE = 'https://api.pinpoint.ng';
const PINPOINT_KEY  = 'pk_live_YOUR_SERVER_KEY';

/** Block checkout if the typed address can't be resolved to a real location. */
add_action('woocommerce_after_checkout_validation', function ($data, $errors) {
    $query = trim(($data['billing_address_1'] ?? '') . ' ' . ($data['billing_city'] ?? ''));
    if ($query === '') {
        return;
    }

    $response = wp_remote_post(PINPOINT_BASE . '/v1/geocode', [
        'headers' => [
            'Authorization' => 'Bearer ' . PINPOINT_KEY,
            'Content-Type'  => 'application/json',
        ],
        'body'    => wp_json_encode(['query' => $query, 'limit' => 1]),
        'timeout' => 8,
    ]);

    if (is_wp_error($response)) {
        return; // fail open — don't block checkout on an API hiccup
    }

    $body = json_decode(wp_remote_retrieve_body($response), true);
    if (empty($body['results'])) {
        $errors->add('billing', 'We could not locate that delivery address. Add a nearby landmark.');
    }
    // On success you could stash $body['results'][0]['code'] on the order meta.
}, 10, 2);
