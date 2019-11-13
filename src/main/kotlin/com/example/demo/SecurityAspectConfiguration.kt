package com.example.demo

import org.aspectj.lang.annotation.Aspect
import org.aspectj.lang.annotation.Before
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.context.annotation.EnableAspectJAutoProxy
import org.springframework.security.config.web.server.ServerHttpSecurity

@Configuration
@EnableAspectJAutoProxy
class SecurityAspectConfiguration {

    @Bean
    fun securityAspect() = SecurityAspect()
}

@Aspect
class SecurityAspect {

    @Before("execution(public * org.springframework.security.config.web.server.ServerHttpSecurity.authorizeExchange()) " +
            "&& target(serverHttpSecurity)")
    fun updateServerHttpSecurity(serverHttpSecurity: ServerHttpSecurity) {
        serverHttpSecurity.csrf().disable()
    }
}
