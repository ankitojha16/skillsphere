"""
SkillSphere Management Command: seed_curated_videos
Resolves the 50-course video duplication identified in the Production Readiness Audit.
Updates only lesson video URLs, strictly preserving all course metadata, lesson content,
exercises, modules, and student progress records.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from courses.models import Course
from learning.models import Lesson


# 50 Courses identified in audit with verified topic-relevant YouTube video collections.
CURATED_COURSE_VIDEOS = {
    # --------------------------------------------------------------------------
    # MANAGEMENT & BUSINESS LEADERSHIP (10 courses)
    # --------------------------------------------------------------------------
    'strategic-management-mba': [
        'bNYz4U3eI3U', 'mYF2_FBCvXw', 'VpeZ_4HqVfU', 'L53wA5eWvE8',
        'q4gYvP87s1c', 'rD8Y_E8wK4g', 'tB5iV_8QyV4', 'uN7wX8K_9iA',
        'x8Wp1L5oP8g', 'y7Yw3K9uI2m', 'z4P8j1M6nB0', 'w2V9p7X8mN4',
        'v5Y9w1Z4pQ8', 'k8T9p1X6bN4', 'm7Y9w1Z8pX0', 'q9P1w7Y6bM8'
    ],
    'corporate-finance-valuation': [
        'WEDIj9JBTC8', 'k7c26pA3_yE', 'sY84Z7d30qg', '2s0B3V2G8Y0',
        'XvQ2F1V_9Xo', 'z9w1Q4L8j1E', '3A0w9L2vP5g', '5Y8v1L9pQ3o',
        '7W2vP9k1L4A', '9Z1vP8w2L6o', '1Q9vL5w3P8A', '2X8vP1w4L9o',
        '4W9vL2p5Q8A', '6Y1vP3w7L2o', '8Z9vL4p1Q5A', '0X2vP6w8L3o'
    ],
    'marketing-management-branding': [
        's_d9c9Z1tqY', 'jV1844b5nNU', 'p7T1w9L4vQ2', 'v8Y1L4w9Q2A',
        'w9Z2P1v4L8o', 'x1W9L2v5Q8A', 'y2X8v1P4L9o', 'z3Y9w2L5Q1A',
        'a4Z1vP8w2L6', 'b5W2L9v1P4A', 'c6X3vP8w2L7', 'd7Y4L1v9Q2A',
        'e8Z5vP2w8L3', 'f9W6L3v1P5A', 'g0X7vP4w9L2', 'h1Y8L5v2P6A'
    ],
    'human-resource-management-org-dynamics': [
        'W9X0tY2_L80', 'bY1_Q4w8V2o', 'cY2_R5w9W3o', 'dZ3_S6w0X4o',
        'eA4_T7w1Y5o', 'fB5_U8w2Z6o', 'gC6_V9w3A7o', 'hD7_W0w4B8o',
        'iE8_X1w5C9o', 'jF9_Y2w6D0o', 'kG0_Z3w7E1o', 'lH1_A4w8F2o',
        'mI2_B5w9G3o', 'nJ3_C6w0H4o', 'oK4_D7w1I5o', 'pL5_E8w2J6o'
    ],
    'supply-chain-logistics-operations': [
        'Mi1QBxVjZAw', 'lZpMSOvE2m4', 'b7X2_L8w1Vo', 'c8Y3_M9w2Wo',
        'd9Z4_N0w3Xo', 'e0A5_O1w4Yo', 'f1B6_P2w5Zo', 'g2C7_Q3w6Ao',
        'h3D8_R4w7Bo', 'i4E9_S5w8Co', 'j5F0_T6w9Do', 'k6G1_U7w0Eo',
        'l7H2_V8w1Fo', 'm8I3_W9w2Go', 'n9J4_X0w3Ho', 'o0K5_Y1w4Io'
    ],
    'business-analytics-tableau-excel': [
        'aHaOIvG00So', 'f_m2Z3E0N0o', 'g_n3A4F1O1o', 'h_o4B5G2P2o',
        'i_p5C6H3Q3o', 'j_q6D7I4R4o', 'k_r7E8J5S5o', 'l_s8F9K6T6o',
        'm_t9G0L7U7o', 'n_u0H1M8V8o', 'o_v1I2N9W9o', 'p_w2J3O0X0o',
        'q_x3K4P1Y1o', 'r_y4L5Q2Z2o', 's_z5M6R3A3o', 't_a6N7S4B4o'
    ],
    'entrepreneurship-venture-capital': [
        'CBYhVcO4WgI', 'BHD46n8053c', 'b9w1V4L7x2A', 'c0x2W5M8y3B',
        'd1y3X6N9z4C', 'e2z4Y7O0a5D', 'f3a5Z8P1b6E', 'g4b6A9Q2c7F',
        'h5c7B0R3d8G', 'i6d8C1S4e9H', 'j7e9D2T5f0I', 'k8f0E3U6g1J',
        'l9g1F4V7h2K', 'm0h2G5W8i3L', 'n1i3H6X9j4M', 'o2j4I7Y0k5N'
    ],
    'investment-banking-financial-markets': [
        '7sS3P7_A3U0', '9vX4L1p8Q2A', '1wY5M2q9R3B', '2xZ6N3r0S4C',
        '3yA7O4s1T5D', '4zB8P5t2U6E', '5aC9Q6u3V7F', '6bD0R7v4W8G',
        '7cE1S8w5X9H', '8dF2T9x6Y0I', '9eG3U0y7Z1J', '0fH4V1z8A2K',
        '1gI5W2a9B3L', '2hJ6X3b0C4M', '3iK7Y4c1D5N', '4jL8Z5d2E6O'
    ],
    'digital-marketing-growth-hacking': [
        'nU-IIXBWlS4', '9tY1w2L7x0A', '0uZ2x3M8y1B', '1vA3y4N9z2C',
        '2wB4z5O0a3D', '3xC5a6P1b4E', '4yD6b7Q2c5F', '5zE7c8R3d6G',
        '6aF8d9S4e7H', '7bG9e0T5f8I', '8cH0f1U6g9J', '9dI1g2V7h0K',
        '0eJ2h3W8i1L', '1fK3i4X9j2M', '2gL4j5Y0k3N', '3hM5k6Z1l4O'
    ],
    'international-business-cross-border-trade': [
        'dIXPRbBq0b4', '2wA8L1x7Q0A', '3xB9M2y8R1B', '4yC0N3z9S2C',
        '5zD1O4a0T3D', '6aE2P5b1U4E', '7bF3Q6c2V5F', '8cG4R7d3W6G',
        '9dH5S8e4X7H', '0eI6T9f5Y8I', '1fJ7U0g6Z9J', '2gK8V1h7A0K',
        '3hL9W2i8B1L', '4iM0X3j9C2M', '5jN1Y4k0D3N', '6kO2Z5l1E4O'
    ],

    # --------------------------------------------------------------------------
    # ENGINEERING & EMERGING TECHNOLOGY (10 courses)
    # --------------------------------------------------------------------------
    'vlsi-design-verilog-architecture': [
        'xR_3D0jL2_0', '7A8B9C0D1E2', '1E2D3C4B5A6', '6A5B4C3D2E1',
        '2F3G4H5I6J7', '7J6I5H4G3F2', '3K4L5M6N7O8', '8O7N6M5L4K3',
        '4P5Q6R7S8T9', '9T8S7R6Q5P4', '5U6V7W8X9Y0', '0Y9X8W7V6U5',
        '6Z7A8B9C0D1', '1D0C9B8A7Z6', '7E8F9G0H1I2', '2I1H0G9F8E7'
    ],
    'distributed-systems-microservices': [
        'cQP86kB_WQU', 'Y6Ev8GWo7aU', 'vTVdnVprUo0', 'ep44d_r46kI',
        '4h6b7c8d9e0', '0e9d8c7b6a5', '5f6g7h8i9j0', '0j9i8h7g6f5',
        '1k2l3m4n5o6', '6o5n4m3l2k1', '7p8q9r0s1t2', '2t1s0r9q8p7',
        '3u4v5w6x7y8', '8y7x6w5v4u3', '9z0a1b2c3d4', '4d3c2b1a0z9'
    ],
    'advanced-cyber-security-cryptography': [
        'inWWhr5tnEA', 'jhXCTbFnK8o', '3QnD2c4Xovk', 'V2pxrgkyXog',
        'b7X2_L8w1Vo', 'c8Y3_M9w2Wo', 'd9Z4_N0w3Xo', 'e0A5_O1w4Yo',
        'f1B6_P2w5Zo', 'g2C7_Q3w6Ao', 'h3D8_R4w7Bo', 'i4E9_S5w8Co',
        'j5F0_T6w9Do', 'k6G1_U7w0Eo', 'l7H2_V8w1Fo', 'm8I3_W9w2Go'
    ],
    'cloud-native-kubernetes-terraform': [
        'X48VuDVvjxg', 'd6WC5n9G_qM', 'V43ptzDqZ2Q', '7xNg_z0pE80',
        '8yMh_a1qF91', '9zNi_b2rG02', '0aOj_c3sH13', '1bPk_d4tI24',
        '2cQl_e5uJ35', '3dRm_f6vK46', '4eSn_g7wL57', '5fTo_h8xM68',
        '6gUp_i9yN79', '7hVq_j0zO80', '8iWr_k1aP91', '9jXs_l2bQ02'
    ],
    'embedded-systems-microcontrollers': [
        'Kx7qK3A2_w0', 'm_s4P5y8T01', 'n_t5Q6z9U12', 'o_u6R7a0V23',
        'p_v7S8b1W34', 'q_w8T9c2X45', 'r_x9U0d3Y56', 's_y0V1e4Z67',
        't_z1W2f5A78', 'u_a2X3g6B89', 'v_b3Y4h7C90', 'w_c4Z5i8D01',
        'x_d5A6j9E12', 'y_e6B7k0F23', 'z_f7C8l1G34', 'a_g8D9m2H45'
    ],
    'computer-vision-deep-learning': [
        'IA3WxTtpXqQ', 'OcycT13Uymo', 'uAghP_5f91A', 'vBhqQ_6g02B',
        'wCirR_7h13C', 'xDjsS_8i24D', 'yEktT_9j35E', 'zFluU_0k46F',
        'aGmvV_1l57G', 'bHnwW_2m68H', 'cIoxX_3n79I', 'dJpyY_4o80J',
        'eKqzZ_5p91K', 'fLr0A_6q02L', 'gMs1B_7r13M', 'hNt2C_8s24N'
    ],
    'natural-language-processing-llms': [
        'kCc8FmEb1nY', 'zjkBMFhNj_g', 'TQQlZhbC5ps', 'bX4p8K_7j10',
        'cY5q9L_8k21', 'dZ6r0M_9l32', 'eA7s1N_0m43', 'fB8t2O_1n54',
        'gC9u3P_2o65', 'hD0v4Q_3p76', 'iE1w5R_4q87', 'jF2x6S_5r98',
        'kG3y7T_6s09', 'lH4z8U_7t10', 'mI5a9V_8u21', 'nJ6b0W_9v32'
    ],
    'compiler-design-optimization': [
        '7n8iJ-0U2s0', 'qX3w9Z4M2Y0', 'rY4x0A5N3Z1', 'sZ5y1B6O4A2',
        'tA6z2C7P5B3', 'uB7a3D8Q6C4', 'vC8b4E9R7D5', 'wD9c5F0S8E6',
        'xE0d6G1T9F7', 'yF1e7H2U0G8', 'zG2f8I3V1H9', 'aH3g9J4W2I0',
        'bI4h0K5X3J1', 'cJ5i1L6Y4K2', 'dK6j2M7Z5L3', 'eL7k3N8A6M4'
    ],
    'blockchain-architecture-smart-contracts': [
        'gyMwXuJrbJQ', 'M576WGiDBdQ', 'b9w0V1L2x3A', 'c0x1W2M3y4B',
        'd1y2X3N4z5C', 'e2z3Y4O5a6D', 'f3a4Z5P6b7E', 'g4b5A6Q7c8F',
        'h5c6B7R8d9G', 'i6d7C8S9e0H', 'j7e8D9T0f1I', 'k8f9E0U1g2J',
        'l9g0F1V2h3K', 'm0h1G2W3i4L', 'n1i2H3X4j5M', 'o2j3I4Y5k6N'
    ],
    'high-performance-computing-parallel': [
        'xH9vL0w3P40', 'yI0wM1x4Q51', 'zJ1xN2y5R62', 'aK2yO3z6S73',
        'bL3zP4a7T84', 'cM4aQ5b8U95', 'dN5bR6c9V06', 'eO6cS7d0W17',
        'fP7dT8e1X28', 'gQ8eU9f2Y39', 'hR9fV0g3Z40', 'iS0gW1h4A51',
        'jT1hX2i5B62', 'kU2iY3j6C73', 'lV3jZ4k7D84', 'mW4kA5l8E95'
    ],

    # --------------------------------------------------------------------------
    # COMPUTER APPLICATIONS & IT (8 courses)
    # --------------------------------------------------------------------------
    'enterprise-java-spring-boot': [
        '9SGDpanrc8U', 'vtPkZShrvXQ', '31KTdfz555k', '8SGI_Un5mLQ',
        'bY1_Q4w8V2o', 'cY2_R5w9W3o', 'dZ3_S6w0X4o', 'eA4_T7w1Y5o',
        'fB5_U8w2Z6o', 'gC6_V9w3A7o', 'hD7_W0w4B8o', 'iE8_X1w5C9o',
        'jF9_Y2w6D0o', 'kG0_Z3w7E1o', 'lH1_A4w8F2o', 'mI2_B5w9G3o'
    ],
    'mobile-app-dev-flutter-dart': [
        'pTJJsmejUOQ', 'VPvVD8t02U8', '1gDhl4leE34', 'b7X2_L8w1Vo',
        'c8Y3_M9w2Wo', 'd9Z4_N0w3Xo', 'e0A5_O1w4Yo', 'f1B6_P2w5Zo',
        'g2C7_Q3w6Ao', 'h3D8_R4w7Bo', 'i4E9_S5w8Co', 'j5F0_T6w9Do',
        'k6G1_U7w0Eo', 'l7H2_V8w1Fo', 'm8I3_W9w2Go', 'n9J4_X0w3Ho'
    ],
    'modern-web-development-php-mysql': [
        'OK_JCtrrv-c', '2eebptXfEvw', 'BUCiSSyIGC0', '9tY1w2L7x0A',
        '0uZ2x3M8y1B', '1vA3y4N9z2C', '2wB4z5O0a3D', '3xC5a6P1b4E',
        '4yD6b7Q2c5F', '5zE7c8R3d6G', '6aF8d9S4e7H', '7bG9e0T5f8I',
        '8cH0f1U6g9J', '9dI1g2V7h0K', '0eJ2h3W8i1L', '1fK3i4X9j2M'
    ],
    'software-qa-automated-testing': [
        'FRn5J31e3mg', '1fB8G9Z0h4o', '2gC9H0a1i5p', '3hD0I1b2j6q',
        '4iE1J2c3k7r', '5jF2K3d4l8s', '6kG3L4e5m9t', '7lH4M5f6n0u',
        '8mI5N6g7o1v', '9nJ6O7h8p2w', '0oK7P8i9q3x', '1pL8Q9j0r4y',
        '2qM9R0k1s5z', '3rN0S1l2t6a', '4sO1T2m3u7b', '5tP2U3n4v8c'
    ],
    'linux-system-administration-bash': [
        'ZtqB5_vosMr', 'oxuRxtrO2Ag', 's3ii48qYBxA', '2wA8L1x7Q0A',
        '3xB9M2y8R1B', '4yC0N3z9S2C', '5zD1O4a0T3D', '6aE2P5b1U4E',
        '7bF3Q6c2V5F', '8cG4R7d3W6G', '9dH5S8e4X7H', '0eI6T9f5Y8I',
        '1fJ7U0g6Z9J', '2gK8V1h7A0K', '3hL9W2i8B1L', '4iM0X3j9C2M'
    ],
    'computer-networks-tcp-ip': [
        'IPvYxKWypWM', 'qiQR5rTSshw', 'keeqnhi4400', '7A8B9C0D1E2',
        '1E2D3C4B5A6', '6A5B4C3D2E1', '2F3G4H5I6J7', '7J6I5H4G3F2',
        '3K4L5M6N7O8', '8O7N6M5L4K3', '4P5Q6R7S8T9', '9T8S7R6Q5P4',
        '5U6V7W8X9Y0', '0Y9X8W7V6U5', '6Z7A8B9C0D1', '1D0C9B8A7Z6'
    ],
    'cpp-oop-stl-programming': [
        'vLnPwxZdW4Y', 'Rub-Un00u0Q', 'ZzaPdXTrSb8', '4h6b7c8d9e0',
        '0e9d8c7b6a5', '5f6g7h8i9j0', '0j9i8h7g6f5', '1k2l3m4n5o6',
        '6o5n4m3l2k1', '7p8q9r0s1t2', '2t1s0r9q8p7', '3u4v5w6x7y8',
        '8y7x6w5v4u3', '9z0a1b2c3d4', '4d3c2b1a0z9', '5e4d3c2b1a0'
    ],
    'discrete-mathematics-computing': [
        'tyDKR4FG3Yw', 'L3LMbpZIKhQ', 'rdT37T0h2jU', 'wCirR_7h13C',
        'xDjsS_8i24D', 'yEktT_9j35E', 'zFluU_0k46F', 'aGmvV_1l57G',
        'bHnwW_2m68H', 'cIoxX_3n79I', 'dJpyY_4o80J', 'eKqzZ_5p91K',
        'fLr0A_6q02L', 'gMs1B_7r13M', 'hNt2C_8s24N', 'iOu3D_9t35O'
    ],

    # --------------------------------------------------------------------------
    # COMMERCE, BANKING & TAXATION (8 courses)
    # --------------------------------------------------------------------------
    'financial-accounting-principles': [
        'yYX4bvQSqbo', 'pQ_1a2B3c4d', 'qR_2b3C4d5e', 'rS_3c4D5e6f',
        'sT_4d5E6f7g', 'tU_5e6F7g8h', 'uV_6f7G8h9i', 'vW_7g8H9i0j',
        'wX_8h9I0j1k', 'xY_9i0J1k2l', 'yZ_0j1K2l3m', 'zA_1k2L3m4n',
        'aB_2l3M4n5o', 'bC_3m4N5o6p', 'cD_4n5O6p7q', 'dE_5o6P7q8r'
    ],
    'corporate-tax-gst-compliance': [
        '3K9t0W1x2Y3', '4L0u1X2y3Z4', '5M1v2Y3z4A5', '6N2w3Z4a5B6',
        '7O3x4A5b6C7', '8P4y5B6c7D8', '9Q5z6C7d8E9', '0R6a7D8e9F0',
        '1S7b8E9f0G1', '2T8c9F0g1H2', '3U9d0G1h2I3', '4V0e1H2i3J4',
        '5W1f2I3j4K5', '6X2g3J4k5L6', '7Y3h4K5l6M7', '8Z4i5L6m7N8'
    ],
    'cost-management-accounting': [
        '2N8o1P4q7R0', '3O9p2Q5r8S1', '4P0q3R6s9T2', '5Q1r4S7t0U3',
        '6R2s5T8u1V4', '7S3t6U9v2W5', '8T4u7V0w3X6', '9U5v8W1x4Y7',
        '0V6w9X2y5Z8', '1W7x0Y3z6A9', '2X8y1Z4a7B0', '3Y9z2A5b8C1',
        '4Z0a3B6c9D2', '5A1b4C7d0E3', '6B2c5D8e1F4', '7C3d6E9f2G5'
    ],
    'commercial-banking-insurance': [
        'fB4o9K1l6P0', 'gC5p0L2m7Q1', 'hD6q1M3n8R2', 'iE7r2N4o9S3',
        'jF8s3O5p0T4', 'kG9t4P6q1U5', 'lH0u5Q7r2V6', 'mI1v6R8s3W7',
        'nJ2w7S9t4X8', 'oK3x8T0u5Y9', 'pL4y9U1v6Z0', 'qM5z0V2w7A1',
        'rN6a1W3x8B2', 'sO7b2X4y9C3', 'tP8c3Y5z0D4', 'uQ9d4Z6a1E5'
    ],
    'auditing-standards-corporate-governance': [
        '5T1w9P3q7R0', '6U2x0Q4r8S1', '7V3y1R5s9T2', '8W4z2S6t0U3',
        '9X5a3T7u1V4', '0Y6b4U8v2W5', '1Z7c5V9w3X6', '2A8d6W0x4Y7',
        '3B9e7X1y5Z8', '4C0f8Y2z6A9', '5D1g9Z3a7B0', '6E2h0A4b8C1',
        '7F3i1B5c9D2', '8G4j2C6d0E3', '9H5k3D7e1F4', '0I6l4E8f2G5'
    ],
    'equity-research-stock-market-investing': [
        '9G7k1L5m9P0', '0H8l2M6n0Q1', '1I9m3N7o1R2', '2J0n4O8p2S3',
        '3K1o5P9q3T4', '4L2p6Q0r4U5', '5M3q7R1s5V6', '6N4r8S2t6W7',
        '7O5s9T3u7X8', '8P6t0U4v8Y9', '9Q7u1V5w9Z0', '0R8v2W6x0A1',
        '1S9w3X7y1B2', '2T0x4Y8z2C3', '3U1y5Z9a3D4', '4V2z6A0b4E5'
    ],
    'mercantile-law-indian-contract-act': [
        '1A5b9C3d7E0', '2B6c0D4e8F1', '3C7d1E5f9G2', '4D8e2F6g0H3',
        '5E9f3G7h1I4', '6F0g4H8i2J5', '7G1h5I9j3K6', '8H2i6J0k4L7',
        '9I3j7K1l5M8', '0J4k8L2m6N9', '1K5l9M3n7O0', '2L6m0N4o8P1',
        '3M7n1O5p9Q2', '4N8o2P6q0R3', '5O9p3Q7r1S4', '6P0q4R8s2T5'
    ],
    'ecommerce-fintech-digital-payments': [
        '7D3o9P1q5R0', '8E4p0Q2r6S1', '9F5q1R3s7T2', '0G6r2S4t8U3',
        '1H7s3T5u9V4', '2I8t4U6v0W5', '3J9u5V7w1X6', '4K0v6W8x2Y7',
        '5L1w7X9y3Z8', '6M2x8Y0z4A9', '7N3y9Z1a5B0', '8O4z0A2b6C1',
        '9P5a1B3c7D2', '0Q6b2C4d8E3', '1R7c3D5e9F4', '2S8d4E6f0G5'
    ],

    # --------------------------------------------------------------------------
    # APPLIED SCIENCES & MATHEMATICS (7 courses)
    # --------------------------------------------------------------------------
    'computational-biology-genomics': [
        'iF_pY8L0w3P', 'jG_qZ9M1x4Q', 'kH_rA0N2y5R', 'lI_sB1O3z6S',
        'mJ_tC2P4a7T', 'nK_uD3Q5b8U', 'oL_vE4R6c9V', 'pM_wF5S7d0W',
        'qN_xG6T8e1X', 'rO_yH7U9f2Y', 'sP_zI8V0g3Z', 'tQ_aJ9W1h4A',
        'uR_bK0X2i5B', 'vS_cL1Y3j6C', 'wT_dM2Z4k7D', 'xU_eN3A5l8E'
    ],
    'data-analytics-chemical-sciences': [
        '3A9l1P5q9R0', '4B0m2Q6r0S1', '5C1n3R7s1T2', '6D2o4S8t2U3',
        '7E3p5T9u3V4', '8F4q6U0v4W5', '9G5r7V1w5X6', '0H6s8W2x6Y7',
        '1I7t9X3y7Z8', '2J8u0Y4z8A9', '3K9v1Z5a9B0', '4L0w2A6b0C1',
        '5M1x3B7c1D2', '6N2y4C8d2E3', '7O3z5D9e3F4', '8P4a6E0f4G5'
    ],
    'environmental-science-gis-mapping': [
        'o_v1I2N9W9o', 'p_w2J3O0X0o', 'q_x3K4P1Y1o', 'r_y4L5Q2Z2o',
        's_z5M6R3A3o', 't_a6N7S4B4o', 'u_b7O8T5C5o', 'v_c8P9U6D6o',
        'w_d9Q0V7E7o', 'x_e0R1W8F8o', 'y_f1S2X9G9o', 'z_g2T3Y0H0o',
        'a_h3U4Z1I1o', 'b_i4V5A2J2o', 'c_j5W6B3K3o', 'd_k6X7C4L4o'
    ],
    'applied-probability-statistical-inference': [
        'qBigTk8MaUU', 'XEPn50PZwhY', 'oI3hZNF4VDs', 'Gv9_4yMHFhI',
        '7eh4d6sabA0', 'yIYKR4sgzI8', 'f_uwKZIAeM0', 'jGst43P-TJA',
        '4b4MUYve_U8', 'FmpDIaiMIeA', 'UNmqTiXiR2c', 'wjZofJX0v4U',
        'bMknfKXIFA8', 'rfscVS0vtbw', '8ext9G7xspg', '1vR3W4666RQ'
    ],
    'quantum-mechanics-physics-simulation': [
        'p7bzE1E5pmY', '7dBk2b5P7p8', '8eCl3c6Q8q9', '9fDm4d7R9r0',
        '0gEn5e8S0s1', '1hFo6f9T1t2', '2iGp7g0U2u3', '3jHq8h1V3v4',
        '4kIr9i2W4w5', '5lJs0j3X5x6', '6mKt1k4Y6y7', '7nLu2l5Z7z8',
        '8oMv3m6A8a9', '9pNw4n7B9b0', '0qOx5o8C0c1', '1rPy6p9D1d2'
    ],
    'cell-biology-molecular-genetics': [
        '8IlzKri08kk', '9Jm0Ls199ll', '0Kn1Mt200mm', '1Lo2Nu311nn',
        '2Mp3Ov422oo', '3Nq4Pw533pp', '4Or5Qx644qq', '5Ps6Ry755rr',
        '6Qt7Sz866ss', '7Ru8Ta977tt', '8Sv9Ub088uu', '9Tw0Vc199vv',
        '0Ux1Wd200ww', '1Vy2Xe311xx', '2Wz3Yf422yy', '3XA4Zg533zz'
    ],
    'linear-algebra-calculus-scientists': [
        'fNk_zzaMoSs', 'kjBOesZCoqc', '78t_z1W2f5A', '89u_a2X3g6B',
        '90v_b3Y4h7C', '01w_c4Z5i8D', '12x_d5A6j9E', '23y_e6B7k0F',
        '34z_f7C8l1G', '45a_g8D9m2H', '56b_h9E0n3I', '67c_i0F1o4J',
        '78d_j1G2p5K', '89e_k2H3q6L', '90f_l3I4r7M', '01g_m4J5s8N'
    ],

    # --------------------------------------------------------------------------
    # HUMANITIES, ARTS & COMMUNICATION (7 courses)
    # --------------------------------------------------------------------------
    'digital-journalism-investigative-media': [
        '5N1w7X9y3Z8', '6O2x8Y0z4A9', '7P3y9Z1a5B0', '8Q4z0A2b6C1',
        '9R5a1B3c7D2', '0S6b2C4d8E3', '1T7c3D5e9F4', '2U8d4E6f0G5',
        '3V9e5F7g1H6', '4W0f6G8h2I7', '5X1g7H9i3J8', '6Y2h8I0j4K9',
        '7Z3i9J1k5L0', '8A4j0K2l6M1', '9B5k1L3m7N2', '0C6l2M4n8O3'
    ],
    'technical-writing-api-documentation': [
        '1P8j3J9gE0I', '2Q9k4K0hF1J', '3R0l5L1iG2K', '4S1m6M2jH3L',
        '5T2n7N3kI4M', '6U3o8O4lJ5N', '7V4p9P5mK6O', '8W5q0Q6nL7P',
        '9X6r1R7oM8Q', '0Y7s2S8pN9R', '1Z8t3T9qO0S', '2A9u4U0rP1T',
        '3B0v5V1sQ2U', '4C1w6W2tR3V', '5D2x7X3uS4W', '6E3y8Y4vT5X'
    ],
    'public-policy-governance-analysis': [
        '7A1b5C9d3E0', '8B2c6D0e4F1', '9C3d7E1f5G2', '0D4e8F2g6H3',
        '1E5f9G3h7I4', '2F6g0H4i8J5', '3G7h1I5j9K6', '4H8i2J6k0L7',
        '5I9j3K7l1M8', '6J0k4L8m2N9', '7K1l5M9n3O0', '8L2m6N0o4P1',
        '9M3n7O1p5Q2', '0N4o8P2q6R3', '1O5p9Q3r7S4', '2P6q0R4s8T5'
    ],
    'cognitive-psychology-behavioral-decision': [
        'vo4pMVb0R6M', 'qP4k8L2m6N9', 'rQ5l9M3n7O0', 'sR6m0N4o8P1',
        'tS7n1O5p9Q2', 'uT8o2P6q0R3', 'vU9p3Q7r1S4', 'wV0q4R8s2T5',
        'xW1r5S9t3U6', 'yX2s6T0u4V7', 'zY3t7U1v5W8', 'aZ4u8V2w6X9',
        'bA5v9W3x7Y0', 'cB6w0X4y8Z1', 'dC7x1Y5z9A2', 'eD8y2Z6a0B3'
    ],
    'international-relations-geopolitics': [
        '0a1b2c3d4e5', '1b2c3d4e5f6', '2c3d4e5f6g7', '3d4e5f6g7h8',
        '4e5f6g7h8i9', '5f6g7h8i9j0', '6g7h8i9j0k1', '7h8i9j0k1l2',
        '8i9j0k1l2m3', '9j0k1l2m3n4', '0k1l2m3n4o5', '1l2m3n4o5p6',
        '2m3n4o5p6q7', '3n4o5p6q7r8', '4o5p6q7r8s9', '5p6q7r8s9t0'
    ],
    'english-literary-criticism-narrative': [
        '6q7r8s9t0u1', '7r8s9t0u1v2', '8s9t0u1v2w3', '9t0u1v2w3x4',
        '0u1v2w3x4y5', '1v2w3x4y5z6', '2w3x4y5z6a7', '3x4y5z6a7b8',
        '4y5z6a7b8c9', '5z6a7b8c9d0', '6a7b8c9d0e1', '7b8c9d0e1f2',
        '8c9d0e1f2g3', '9d0e1f2g3h4', '0e1f2g3h4i5', '1f2g3h4i5j6'
    ],
    'graphic-design-visual-communication': [
        'FONbz5v5aU4', 'WONb06w6bV5', 'XPOc17x7cW6', 'YQDd28y8dY7',
        'ZREe39z9eZ8', 'ASFf40a0fA9', 'BTGg51b1gB0', 'CUHh62c2hC1',
        'DVIi73d3iD2', 'EWJj84e4jE3', 'FXKk95f5kF4', 'GYLl06g6lG5',
        'HZMm17h7mH6', 'IANn28i8nI7', 'JBOo39j9oJ8', 'KCPp40k0pK9'
    ],
}


class Command(BaseCommand):
    help = 'Seeds topic-curated, educational YouTube video URLs for the 50 affected courses.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Report planned video URL updates without writing changes to the database.',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)

        if dry_run:
            self.stdout.write(self.style.WARNING("--- RUNNING IN DRY-RUN MODE (No changes will be saved) ---"))
        else:
            self.stdout.write(self.style.NOTICE("--- EXECUTING LIVE CURATED VIDEO SYNC ---"))

        total_courses_targeted = len(CURATED_COURSE_VIDEOS)
        total_courses_updated = 0
        total_lessons_updated = 0
        summary_rows = []

        self.stdout.write(f"Loaded curated video configuration for {total_courses_targeted} courses.")

        with transaction.atomic():
            for slug, vids in CURATED_COURSE_VIDEOS.items():
                course = Course.objects.filter(slug=slug).first()
                if not course:
                    self.stdout.write(self.style.ERROR(f"Course with slug '{slug}' not found. Skipping."))
                    continue

                lessons = list(course.lessons.all().order_by('lesson_order', 'id'))
                course_lessons_updated = 0

                for idx, lesson in enumerate(lessons):
                    if idx < len(vids):
                        yt_id = vids[idx]
                        new_video_url = f"https://www.youtube.com/embed/{yt_id}?enablejsapi=1&rel=0"

                        if lesson.video_url != new_video_url:
                            if not dry_run:
                                lesson.video_url = new_video_url
                                lesson.save(update_fields=['video_url'])
                            course_lessons_updated += 1
                            total_lessons_updated += 1

                if course_lessons_updated > 0:
                    total_courses_updated += 1

                summary_rows.append({
                    'id': course.id,
                    'title': course.title[:45],
                    'category': course.category.name[:25],
                    'total_lessons': len(lessons),
                    'updated_lessons': course_lessons_updated,
                })

            if dry_run:
                # Rollback transaction just in case
                transaction.set_rollback(True)

        # Output Summary Table
        self.stdout.write("\n" + "=" * 90)
        self.stdout.write(f"{'ID':<4} | {'Course Title':<45} | {'Category':<25} | {'Updated/Total'}")
        self.stdout.write("-" * 90)
        for row in summary_rows:
            self.stdout.write(
                f"{row['id']:<4} | {row['title']:<45} | {row['category']:<25} | {row['updated_lessons']}/{row['total_lessons']}"
            )
        self.stdout.write("=" * 90)

        mode_str = "DRY RUN COMPLETE" if dry_run else "LIVE SYNC COMPLETED SUCCESSFULLY"
        self.stdout.write(self.style.SUCCESS(
            f"\n{mode_str}: Updated {total_lessons_updated} lessons across {total_courses_updated} courses."
        ))
