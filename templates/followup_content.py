"""
Follow-up email content templates for different countries and recipient types.
"""

# Follow-up introduction templates based on recipient type
FOLLOWUP_INTROS = {
    'municipality': {
        'first': "I hope this email finds you well. I recently reached out regarding our smart waste management solutions for municipalities. Given your city's commitment to sustainability and smart city initiatives, I wanted to ensure you received our information about the SN10 smart waste sensor.",
        'second': "I'm following up on my previous email about SensIQ's smart waste management solutions. Many municipalities we work with have found our technology instrumental in optimizing their waste collection operations and achieving their sustainability goals.",
        'third': "I wanted to touch base one final time regarding our smart waste management solution. We've helped several municipalities achieve significant cost savings and operational improvements in their waste management programs."
    },
    'charity': {
        'first': "I hope this email finds you well. I recently reached out regarding our smart waste management solutions for charitable organizations. Given your organization's commitment to sustainability and community impact, I wanted to ensure you received our information about the SN10 smart waste sensor.",
        'second': "I'm following up on my previous email about SensIQ's smart waste management solutions. Many charitable organizations we work with have found our technology instrumental in optimizing their operations and reducing waste management costs.",
        'third': "I wanted to touch base one final time regarding our smart waste management solution. We've helped several charitable organizations achieve significant cost savings and operational improvements in their waste management programs."
    },
    'waste_management': {
        'first': "I hope you're having a great week. I recently shared information about our SN10 smart waste sensor solution. As a waste management professional, I believe you'll find our technology particularly relevant to optimizing collection routes and reducing operational costs.",
        'second': "I'm following up on my previous message about our smart waste management technology. Many waste management companies have reported 30%+ reduction in collection costs after implementing our solution.",
        'third': "I wanted to reach out one last time about our smart waste sensor technology. We've helped numerous waste management companies transform their operations with data-driven insights."
    },
    'property_management': {
        'first': "I hope this email finds you well. I recently reached out about our smart waste management solution for property managers. Our technology has been helping property management companies optimize their waste services and reduce costs.",
        'second': "I'm following up on my previous email about SensIQ's smart waste solutions. Many property management companies we work with have significantly improved their waste management efficiency and tenant satisfaction.",
        'third': "I wanted to touch base one final time regarding our smart waste management solution. We've helped several property management companies achieve better waste service optimization and cost control."
    }
}

# Country-specific content
COUNTRY_CONTENT = {
    'UAE': {
        'municipality': {
            'content': """In line with the UAE's Vision 2030 and smart city initiatives, our solution helps municipalities transform their waste management operations. Our system supports UAE's sustainability goals and smart city transformation while reducing carbon emissions from waste collection vehicles. We help improve public space cleanliness in line with UAE's high standards and generate valuable data-driven insights for better urban planning.""",
            'cta': "Would you be interested in seeing how other UAE municipalities have implemented our solution?"
        },
        'charity': {
            'content': """Supporting UAE's vision for sustainable development and community welfare, our solution helps charitable organizations optimize their waste management operations. Our system enables cost-effective waste management while supporting your organization's environmental and social impact goals. We help improve operational efficiency and reduce costs, allowing you to focus more resources on your charitable mission.""",
            'cta': "Would you like to see how other charitable organizations in the UAE have benefited from our solution?"
        },
        'waste_management': {
            'content': """As the UAE focuses on sustainability and efficient waste management, our solution provides comprehensive optimization capabilities. Our system helps optimize routes based on real-time fill levels and significantly reduce fuel consumption and vehicle emissions. We ensure compliance with municipality requirements for smart waste solutions while supporting UAE's circular economy initiatives.""",
            'cta': "Would you like to discuss how our solution can help you meet UAE's evolving waste management standards?"
        },
        'property_management': {
            'content': """For UAE's premium properties and developments, our smart waste management solution delivers exceptional value. We help enhance property value through advanced waste management systems and improve tenant satisfaction with consistently clean waste areas. Our solution helps meet UAE's high standards for property management while supporting green building certifications.""",
            'cta': "Would you be interested in seeing how other UAE properties have benefited from our solution?"
        }
    },
    'KSA': {
        'municipality': {
            'content': """Supporting Saudi Vision 2030 and smart city development, our solution empowers municipalities to achieve their digital transformation goals. We align perfectly with KSA's smart city transformation objectives and support comprehensive waste management digitalization initiatives. Our system helps improve urban cleanliness and operational efficiency while generating valuable data for smart city planning.""",
            'cta': "Would you like to learn how our solution supports KSA's smart city vision?"
        },
        'charity': {
            'content': """Supporting KSA's Vision 2030 and its focus on community development, our solution helps charitable organizations optimize their waste management operations. Our system enables efficient and sustainable waste management while supporting your organization's community service goals. We help improve operational efficiency and reduce costs, maximizing the impact of your charitable activities.""",
            'cta': "Would you like to see how our solution can support your charitable organization's operations in KSA?"
        },
        'waste_management': {
            'content': """Supporting KSA's waste management modernization efforts, our solution is designed to meet new smart city requirements and optimize operations in Saudi Arabia's challenging climate. We help support waste reduction and recycling initiatives while providing comprehensive data for regulatory compliance, ensuring your operations stay ahead of evolving standards.""",
            'cta': "Would you be interested in seeing how our solution performs in Saudi Arabia's environment?"
        },
        'property_management': {
            'content': """For KSA's modern properties and developments, including ambitious projects like NEOM, our solution provides cutting-edge waste management capabilities. We help meet new property management standards while enhancing property value through smart solutions. Our system ensures improved waste management efficiency aligned with KSA's vision for modern urban development.""",
            'cta': "Would you like to see how our solution fits with KSA's modern property developments?"
        }
    },
    'India': {
        'municipality': {
            'content': """Supporting the Swachh Bharat Mission and Smart Cities Mission, our solution helps municipalities achieve their cleanliness and digitalization goals. We align perfectly with India's municipal solid waste management guidelines while enhancing city cleanliness and waste collection efficiency. Our system provides valuable data for smart city initiatives, helping transform urban waste management.""",
            'cta': "Would you like to see how our solution aligns with India's smart city and cleanliness missions?"
        },
        'charity': {
            'content': """Supporting India's commitment to cleanliness and sustainable development, our solution helps charitable organizations optimize their waste management operations. Our system enables cost-effective waste management while supporting your organization's social impact goals. We help improve operational efficiency and reduce costs, allowing you to maximize your charitable impact in the community.""",
            'cta': "Would you like to learn how our solution can enhance your charitable organization's operations in India?"
        },
        'waste_management': {
            'content': """Supporting India's waste management modernization efforts, our solution helps meet new solid waste management rules while optimizing operations in diverse urban environments. We enable better support for segregation and recycling initiatives while providing comprehensive compliance data for regulatory requirements, ensuring your operations meet evolving standards.""",
            'cta': "Would you be interested in seeing how our solution can enhance your waste management operations in India?"
        },
        'property_management': {
            'content': """For India's modern properties and developments, particularly in Smart City residential projects, our solution delivers significant value. We help meet new waste management regulations while enhancing property value through smart solutions. Our system ensures improved waste collection efficiency aligned with India's vision for modern urban living.""",
            'cta': "Would you like to learn how our solution can benefit your property management operations in India?"
        }
    }
}

# Main content templates based on follow-up stage
MAIN_CONTENT = {
    'first': """I understand you're busy, but I wanted to highlight a few key benefits of our solution:

✅ Real-time fill level monitoring – Real-time monitoring and optimization
✅ Route optimization for collection efficiency – Reduce operational costs by up to 30%
✅ Significant cost reduction potential – Enhance service quality and impact
✅ Easy integration with existing systems – Advanced analytics and reporting

We're currently offering a free pilot program to demonstrate these benefits in your specific context.""",
    
    'second': """I wanted to share some recent success metrics from our clients:

✅ 30% average reduction in collection costs – Proven cost savings
✅ 40% improvement in route efficiency – Optimized operations
✅ Real-time monitoring of all waste points – Complete visibility
✅ Quick ROI through operational savings – Rapid value realization

We can provide similar results for your operations through our free pilot program.""",
    
    'third': """Before I close this conversation, I wanted to share that we're currently offering:

✅ Free site assessment and ROI calculation – No upfront cost
✅ 3-month pilot program with no commitment – Risk-free trial
✅ Special pricing for early adopters – Limited time offer
✅ Full support during implementation – Seamless integration

If you're interested in exploring these opportunities, I'm happy to schedule a brief call at your convenience."""
}

def get_followup_content(country, recipient_type, followup_stage):
    """
    Get the appropriate follow-up email content based on country, recipient type, and follow-up stage.
    
    Args:
        country (str): Country code ('UAE', 'KSA', 'India')
        recipient_type (str): Type of recipient ('municipality', 'charity')
        followup_stage (str): Stage of follow-up ('first', 'second', 'third')
        
    Returns:
        dict: Dictionary containing email content components
    """
    # Validate country
    if country not in COUNTRY_CONTENT:
        print(f"Warning: Invalid country {country}, defaulting to UAE")
        country = 'UAE'

    # Validate recipient type
    valid_recipient_types = ['municipality', 'charity']
    if recipient_type not in valid_recipient_types:
        print(f"Warning: Invalid recipient type {recipient_type}, defaulting to municipality")
        recipient_type = 'municipality'

    # Validate followup stage
    valid_stages = ['first', 'second', 'third']
    if followup_stage not in valid_stages:
        print(f"Warning: Invalid followup stage {followup_stage}, defaulting to first")
        followup_stage = 'first'

    # Get content components
    followup_intro = FOLLOWUP_INTROS[recipient_type][followup_stage]
    country_content = COUNTRY_CONTENT[country][recipient_type]
    main_content = MAIN_CONTENT[followup_stage]

    return {
        'followup_intro': followup_intro,
        'country_specific_content': country_content['content'],
        'main_content': main_content,
        'cta_message': country_content['cta']
    } 